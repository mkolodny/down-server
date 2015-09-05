from __future__ import unicode_literals
from datetime import datetime, timedelta
import json
from urllib import urlencode
from django.conf import settings
from django.contrib import auth
from django.contrib.gis.measure import D
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import render
from django.views.generic.base import RedirectView, TemplateView
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
    LinfootFunnelSerializer,
    PhoneSerializer,
    SessionSerializer,
    SocialAccountSyncSerializer,
    UserSerializer,
    UserPhoneSerializer,
)
from .utils import get_facebook_friends, get_facebook_profile
from down.apps.events.models import Event, Invitation
from down.apps.events.serializers import (
    EventSerializer,
    InvitationSerializer,
    MyInvitationSerializer,
)
from down.apps.friends.models import Friendship
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
            facebook_friends = get_facebook_friends(social_account)
            serializer = FriendSerializer(facebook_friends, many=True)
            friends = serializer.data
        except SocialAccount.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(friends)

    @list_route(methods=['get'])
    def invitations(self, request):
        twenty_four_hrs_ago = datetime.now(pytz.utc) - timedelta(hours=24)
        invitations = Invitation.objects.filter(to_user=request.user) \
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

        try:
            account = SocialAccount.objects.get(user=request.user)
            account.profile['access_token'] = access_token
            account.save()
        except SocialAccount.DoesNotExist:
            profile = get_facebook_profile(access_token)

            # TODO: Check whether a social account already exists with that
            # facebook id. If it does, log in as the user from that social account.
            # Update the userphone to point to that user. Delete the current user.

            # Update the user.
            # Facebook users might not have emails.
            request.user.email = profile.get('email')
            request.user.name = profile['name']
            request.user.first_name = profile['first_name']
            request.user.last_name = profile['last_name']
            request.user.image_url = profile['image_url']
            request.user.save()

            # Create the user's social account.
            account = SocialAccount(user_id=request.user.id, provider=provider,
                                    uid=profile['id'], profile=profile)
            account.save()

        facebook_friends = get_facebook_friends(account)
        data = {'facebook_friends': facebook_friends}
        serializer = UserSerializer(request.user, context=data)
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
        url = '{meteor_url}/users'.format(meteor_url=settings.METEOR_URL)
        data = json.dumps({
            'user_id': user.id,
            'password': token.key,
        })
        auth_header = 'Token {api_key}'.format(api_key=settings.METEOR_KEY)
        headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/json',
        }
        response = requests.post(url, data=data, headers=headers)
        if response.status_code != 200:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)

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
        profile = get_facebook_profile(access_token)

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

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserPhoneViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = UserPhone.objects.all()
    serializer_class = UserPhoneSerializer

    @list_route(methods=['post'])
    def phones(self, request):
        """
        Return a list of users with the given phone numbers.

        We're using POST here mainly because the list of phone numbers may not
        be able to fit in the query parameters of a GET request.
        """
        # TODO: Handle when the data is invalid.
        serializer = PhoneSerializer(data=request.data)
        serializer.is_valid()

        # Filter user phone numbers using the phone number data.
        phones = serializer.data['phones']
        user_phones = UserPhone.objects.filter(phone__in=phones)
        user_phones.prefetch_related('user')

        serializer = UserPhoneSerializer(user_phones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @list_route(methods=['post'])
    def contact(self, request):
        """
        Create a userphone, and a user with the given name.
        """
        serializer = ContactSerializer(data=request.data)
        serializer.is_valid()

        # Create a user with the given name
        user = User(name=serializer.data['name'])
        user.save()

        # Create a userphone for the new user.
        phone = serializer.data['phone']
        try:
            user_phone = UserPhone.objects.get(phone=phone)
            status_code = status.HTTP_200_OK
        except UserPhone.DoesNotExist:
            user_phone = UserPhone(user=user, phone=phone)
            user_phone.save()
            status_code = status.HTTP_201_CREATED

        # Text the contact to let them know that the user added them.
        client = TwilioRestClient(settings.TWILIO_ACCOUNT, settings.TWILIO_TOKEN)
        message = ('{name} (@{username}) added you as a friend on Down!'
                   ' - http://down.life/app').format(name=request.user.name,
                                                     username=request.user.username)
        client.messages.create(to=phone, from_=settings.TWILIO_PHONE,
                               body=message)

        serializer = UserPhoneSerializer(user_phone)
        return Response(serializer.data, status=status_code)


class LinfootFunnelViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = LinfootFunnel.objects.all()
    serializer_class = LinfootFunnelSerializer
