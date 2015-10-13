from __future__ import unicode_literals
from datetime import datetime, timedelta
import json
import time
from urllib import urlencode
from django.conf import settings
from django.contrib import auth
from django.contrib.gis.measure import D
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import render
from django.views.generic.base import RedirectView, TemplateView
from hashids import Hashids
import pytz
import requests
from rest_framework import mixins, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import detail_route, list_route
from rest_framework.filters import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from twilio import TwilioRestException
from twilio.rest import TwilioRestClient
from .filters import UserFilter
from .models import AuthCode, LinfootFunnel, SocialAccount, User, UserPhone
from .permissions import IsCurrentUserOrReadOnly
from .serializers import (
    AuthCodeSerializer,
    ContactSerializer,
    FacebookSessionSerializer,
    FriendSerializer,
    FriendSelectedSerializer,
    LinfootFunnelSerializer,
    MatchSerializer,
    SessionSerializer,
    SocialAccountSyncSerializer,
    UserSerializer,
    UserPhoneSerializer,
)
from . import utils
from down.apps.events.models import Event, Invitation
from down.apps.events.serializers import (
    EventSerializer,
    InvitationSerializer,
    MyInvitationSerializer,
)
from down.apps.friends.models import Friendship
from down.apps.notifications.utils import send_message
from down.apps.utils.exceptions import ServiceUnavailable


class UserViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin,
                  mixins.UpdateModelMixin, viewsets.GenericViewSet):
    authentication_classes = (TokenAuthentication,)
    filter_backends = (DjangoFilterBackend,)
    filter_class = UserFilter
    permission_classes = (IsAuthenticated, IsCurrentUserOrReadOnly)
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @list_route(methods=['get'])
    def friends(self, request, pk=None):
        # TODO: Handle when the user doesn't exist.
        serializer = FriendSerializer(request.user.friends, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'], url_path='facebook-friends')
    def facebook_friends(self, request, pk=None):
        """
        Get a list of the user's facebook friends.
        """
        try:
            social_account = SocialAccount.objects.get(user=request.user)
            facebook_friends = utils.get_facebook_friends(social_account)
            serializer = FriendSerializer(facebook_friends, many=True)
            friends = serializer.data
        except SocialAccount.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(friends)

    @list_route(methods=['get'], url_path='invitations')
    def joined_invitations(self, request):
        twenty_four_hrs_ago = datetime.now(pytz.utc) - timedelta(hours=24)
        joined_responses = [Invitation.ACCEPTED, Invitation.MAYBE]
        invitations = Invitation.objects.filter(to_user=request.user,
                                                response__in=joined_responses) \
                .select_related('event') \
                .filter(Q(event__datetime__isnull=True,
                          event__created_at__gt=twenty_four_hrs_ago) |
                        Q(event__datetime__isnull=False,
                          event__datetime__gt=twenty_four_hrs_ago)) \
                .select_related('from_user')

        serializer = MyInvitationSerializer(invitations, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @list_route(methods=['get'], url_path='added-me')
    def added_me(self, request):
        """
        Get a list of users who added the user as their friend. Only include users
        whose friendship the user hasn't ackowledged yet - either by adding the
        user back, or deleting the added me notification.
        """
        added_me = Friendship.objects.filter(friend=request.user)
        added_me_ids = [friendship.user_id for friendship in added_me]
        added = Friendship.objects.filter(user=request.user,
                                          friend_id__in=added_me_ids)
        added_ids = set(friendship.friend_id for friendship in added)
        new_added_me = [friendship.user for friendship in added_me
                        if friendship.user_id not in added_ids]

        serializer = FriendSerializer(new_added_me, many=True)
        return Response(serializer.data)

    @list_route(methods=['post'])
    def match(self, request):
        """
        Send the first user who selected their friend a push notification about a
        match.
        """
        serializer = MatchSerializer(data=request.data)
        serializer.is_valid()

        friend_id = serializer.data['first_user']
        friend = User.objects.get(id=friend_id)
        message = 'You and {name} are both down to do something!'.format(
                name=friend.name)
        send_message([friend_id], message, sms=False)

        return Response()

    @list_route(methods=['post'], url_path='friend-select')
    def friend_select(self, request):
        """
        Send a user a push notification letting them know that one of their friends
        are down to hang out.
        """
        serializer = FriendSelectedSerializer(data=request.data)
        serializer.is_valid()

        user_id = serializer.data['user']
        friend_id = serializer.data['friend']
        try:
            # Make sure the friend has added the user back.
            Friendship.objects.get(user_id=friend_id, friend_id=user_id)
            message = 'One of your friends is down to hang out with you.'
            send_message([friend_id], message, sms=False)

            return Response()
        except Friendship.DoesNotExist:
            return Response(status=status.HTTP_403_FORBIDDEN)


class UserUsernameDetail(APIView):

    def get(self, request, username=None):
        try:
            User.objects.get(username__iexact=username)
            return Response()
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class SocialAccountSync(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        # TODO: Handle when the data is invalid.
        serializer = SocialAccountSyncSerializer(data=request.data)
        serializer.is_valid()

        # Request the user's profile from the selected provider.
        provider = serializer.data['provider']
        access_token = serializer.data['access_token']

        # Save the user's current auth token and user object.
        token = request.auth
        user = request.user

        try:
            social_account = SocialAccount.objects.get(user=request.user)
            social_account.profile['access_token'] = access_token
            social_account.save()
        except SocialAccount.DoesNotExist:
            profile = utils.get_facebook_profile(access_token)

            try:
                # When a user has logged into the web view, and just installed the
                # app, they'll have a social account tied to a different user
                # object.
                social_account = SocialAccount.objects.get(uid=profile['id'])

                # The user has logged into the web view, and just installed the
                # app. Return the user's token from that social account.
                user = social_account.user
                token = Token.objects.get(user=user)

                # Then update their userphone to point to that user
                UserPhone.objects.filter(user=request.user).update(user=user)

                # Delete the current user.
                request.user.delete()

                # Log in to the meteor server as the new user.
                utils.meteor_login(user.id, token)
            except SocialAccount.DoesNotExist:
                # Update the user with the new data from Facebook.
                # Facebook users might not have emails.
                request.user.email = profile.get('email')
                request.user.name = profile['name']
                request.user.first_name = profile['first_name']
                request.user.last_name = profile['last_name']
                request.user.image_url = profile['image_url']
                request.user.save()

                # Create the user's social account.
                social_account = SocialAccount(user_id=request.user.id,
                                               provider=provider,
                                               uid=profile['id'], profile=profile)
                social_account.save()

        facebook_friends = utils.get_facebook_friends(social_account)
        data = {'facebook_friends': facebook_friends, 'authtoken': token.key}
        serializer = UserSerializer(user, context=data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AuthCodeViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = AuthCode.objects.all()
    serializer_class = AuthCodeSerializer

    def create(self, request, *args, **kwargs):
        # Make sure the client has set the API version. This ensures that logins
        # from a beta version of the app won't work.
        if not request.version:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)

        # If the user is the Apple test user, fake a good response.
        if request.data.get('phone') == '+15555555555':
            return Response(status=status.HTTP_201_CREATED)

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            self.send_auth_sms(serializer.data['code'], serializer.data['phone'])
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)

        elif serializer.errors.get('phone') == ['This field must be unique.']:
            # We don't want to create/serialize a new authcode if one already exists
            # TODO: Impement scheduled deletion of authcodes by "created_at"
            # timestamp.
            auth = AuthCode.objects.get(phone=request.data['phone'])
            self.send_auth_sms(auth.code, request.data['phone'])
            return Response(status=status.HTTP_200_OK)

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def send_auth_sms(self, auth_code, phone):
        # Text the user their auth code.
        client = TwilioRestClient(settings.TWILIO_ACCOUNT, settings.TWILIO_TOKEN)
        message = 'Your Down code: {}'.format(auth_code)
        try:
            client.messages.create(to=phone, from_=settings.TWILIO_PHONE,
                                   body=message)
        except TwilioRestException:
            raise ServiceUnavailable('Twilio\'s shitting the bed...')
    

class SessionViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):

    def create(self, request, *args, **kwargs):
        # TODO: Handle when the data is invalid.
        serializer = SessionSerializer(data=request.data)
        serializer.is_valid()

        try:
            auth = AuthCode.objects.get(phone=serializer.data['phone'], 
                                        code=serializer.data['code'])
        except AuthCode.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # Get or create the user
        try:
            # Init the user's facebook friends.
            phone = serializer.data['phone']
            user_number = UserPhone.objects.get(phone=phone)

            # User exists
            user = user_number.user
            token, created = Token.objects.get_or_create(user=user)
        except UserPhone.DoesNotExist:
            # User doesn't already exist, so create a blank new user and phone
            # number.
            user = User()
            user.save()

            userphone = UserPhone(user=user, phone=serializer.data['phone'])
            userphone.save()

            token = Token.objects.create(user=user)

        # Authenticate the user on the meteor server.
        utils.meteor_login(user.id, token)

        # If the user is the Apple test user, don't delete the auth code.
        if serializer.data['phone'] != '+15555555555':
            auth.delete()

        data = {'authtoken': token.key}
        serializer = UserSerializer(user, context=data)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @list_route(methods=['post'])
    def facebook(self, request):
        # TODO: Handle when the data is invalid.
        serializer = FacebookSessionSerializer(data=request.data)
        serializer.is_valid()

        access_token = serializer.data['access_token']
        profile = utils.get_facebook_profile(access_token)

        try:
            social_account = SocialAccount.objects.get(uid=profile['id'])
            user = social_account.user
        except SocialAccount.DoesNotExist:
            user = User(email=profile.get('email'), name=profile['name'],
                        first_name=profile['first_name'],
                        last_name=profile['last_name'],
                        image_url=profile['image_url'])
            user.save()
            social_account = SocialAccount(user=user,
                                           provider=SocialAccount.FACEBOOK,
                                           uid=profile['id'], profile=profile)
            social_account.save()

        # Log in to the meteor server.
        token, created = Token.objects.get_or_create(user=user)
        utils.meteor_login(user.id, token)

        context = {'authtoken': token.key}
        serializer = UserSerializer(user, context=context)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserPhoneViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = UserPhone.objects.all()
    serializer_class = UserPhoneSerializer

    @list_route(methods=['post'])
    def contacts(self, request):
        """
        Return a list of userphones with the given phone numbers. Create
        userphones for any contacts without userphones.
        """
        # TODO: Handle when the data is invalid.
        contacts = request.data['contacts']
        serializer = ContactSerializer(data=contacts, many=True)
        serializer.is_valid()

        # Filter user phone numbers using the phone number data.
        phones = [contact['phone'] for contact in serializer.data]
        userphones = UserPhone.objects.filter(phone__in=phones)
        userphones.prefetch_related('user')

        # Create userphones for any contacts who don't have userphones yet. First,
        # we create users with the contacts' names. Then we create userphones for
        # each user. `bulk_ref` is used to query for the objects we bulk created,
        # since Django doesn't set ids on objects that were bulk created.
        phones_set = {unicode(userphone.phone) for userphone in userphones}
        userless_contacts = [contact for contact in contacts
                             if contact['phone'] not in phones_set]
        if len(userless_contacts) > 0:
            # Create the `bulk_ref` for querying the objects we bulk create.
            hashids = Hashids(salt=settings.HASHIDS_SALT)
            timestamp = int(time.time())
            bulk_ref = hashids.encode(request.user.id, timestamp)

            # Create users for contacts without userphones.
            contacts_users = [User(name=contact['name'], bulk_ref=bulk_ref)
                              for contact in userless_contacts]
            User.objects.bulk_create(contacts_users)
            contacts_users = User.objects.filter(bulk_ref=bulk_ref)

            # Create userphones for the users we created.
            # contacts_dict == {'Andrew': ['+19251234567', '+19252234456'], ...}
            contacts_dict = {}
            for contact in userless_contacts:
                name = contact['name']
                contacts_dict[name] = contacts_dict.get(name, [])
                contacts_dict[name].append(contact['phone'])
            contacts_userphones = []
            for user in contacts_users:
                phone = contacts_dict[user.name].pop()
                userphone = UserPhone(user=user, phone=phone, bulk_ref=bulk_ref)
                contacts_userphones.append(userphone)
            UserPhone.objects.bulk_create(contacts_userphones)
            contacts_userphones = UserPhone.objects.filter(bulk_ref=bulk_ref)
            contacts_userphones.prefetch_related('user')
            
            # Merge the new contacts' userphones and the existing userphones.
            userphones = list(userphones)
            userphones.extend(list(contacts_userphones))

        serializer = UserPhoneSerializer(userphones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LinfootFunnelViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = LinfootFunnel.objects.all()
    serializer_class = LinfootFunnelSerializer
