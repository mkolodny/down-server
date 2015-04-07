from __future__ import unicode_literals
from urllib import urlencode
import uuid
from django.conf import settings
from django.contrib import auth
from django.shortcuts import render
from django.views.generic.base import RedirectView, TemplateView
from firebase_token_generator import create_token
import requests
from rest_framework import mixins, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import detail_route, list_route
from rest_framework.filters import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from twilio.rest import TwilioRestClient
from .exceptions import ServiceUnavailable
from .models import AuthCode, LinfootFunnel, SocialAccount, User, UserPhoneNumber
from .permissions import IsCurrentUserOrReadOnly
from .serializers import (
    AuthCodeSerializer,
    LinfootFunnelSerializer,
    PhoneSerializer,
    SessionSerializer,
    SocialAccountLoginSerializer,
    UserSerializer,
    UserPhoneNumberSerializer,
)
from down.apps.auth.filters import UserFilter
from down.apps.events.models import Event, Invitation
from down.apps.events.serializers import EventSerializer
from down.apps.friends.models import Friendship


class UserViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin,
                  mixins.UpdateModelMixin, viewsets.GenericViewSet):
    authentication_classes = (TokenAuthentication,)
    filter_backends = (DjangoFilterBackend,)
    filter_class = UserFilter
    permission_classes = (IsAuthenticated, IsCurrentUserOrReadOnly)
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @detail_route(methods=['get'])
    def friends(self, request, pk=None):
        # TODO: Handle when the user doesn't exist.
        user = User.objects.get(id=pk)
        serializer = UserSerializer(user.friends, many=True)
        return Response(serializer.data)

    @detail_route(methods=['get'])
    def facebook_friends(self, request, pk=None):
        """
        Get a list of the user's facebook friends.
        """
        # Ask Facebook for the user's Facebook friends who are using Down.
        user_facebook_account = SocialAccount.objects.get(user=request.user)
        params = {'access_token': user_facebook_account.profile['access_token']}
        url = 'https://graph.facebook.com/v2.2/me/friends?' + urlencode(params)
        r = requests.get(url)
        if r.status_code != status.HTTP_200_OK:
            raise ServiceUnavailable(r.content)
        try:
            facebook_json = r.json()
        except ValueError:
            raise ServiceUnavailable('Facebook response data was not JSON.')
        try:
            facebook_friends = facebook_json['data']
        except KeyError:
            raise ServiceUnavailable('Facebook response did not contain data.')

        # Use the list of the user's Facebook friends to create a queryset of the
        # user's friends on Down.
        friend_ids = []
        for facebook_friend in facebook_friends:
            # TODO: Figure out how to create multiple facebook apps for separate
            # environments. Right now, since the main facebook app is being
            # shared across all of our environments, facebook may think our users
            # have friends on Down that are on a different environment.
            # Making sure the friend exists is a hack to handle that problem until
            # we create multiple facebook apps/environments.
            try:
                account = SocialAccount.objects.get(uid=facebook_friend['id'])
                friend_ids.append(account.user_id)
            except SocialAccount.DoesNotExist:
                continue
        friends = User.objects.filter(id__in=friend_ids)
        serializer = UserSerializer(friends, many=True)
        return Response(serializer.data)

    @detail_route(methods=['get'])
    def invited_events(self, request, pk=None):
        invitations = Invitation.objects.filter(to_user=request.user)
        event_ids = [invitation.event_id for invitation in invitations]
        events = Event.objects.filter(id__in=event_ids)
        events.prefetch_related('place')
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserUsernameDetail(APIView):

    def get(self, request, username=None):
        try:
            User.objects.get(username=username)
            return Response()
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class SocialAccountLogin(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        # TODO: Handle when the data is invalid.
        serializer = SocialAccountLoginSerializer(data=request.data)
        serializer.is_valid()

        # Request the user's profile from the selected provider.
        provider = serializer.data['provider']
        access_token = serializer.data['access_token']
        profile = self.get_profile(provider, access_token)

        # Check whether the user has already signed up.
        try:
            user = User.objects.get(email=profile['email'])
            
            # Update all of the new user's objects to point to the old user, and
            # delete the new user.
            phone = UserPhoneNumber.objects.get(user=request.user)
            phone.user = user
            phone.save()
            request.user.delete()
            request.auth.user = user
            request.auth.save()

            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            # Update the user.
            request.user.email = profile['email']
            request.user.name = profile['name']
            request.user.image_url = profile['image_url']
            request.user.save()

            # Create the user's social account.
            account = SocialAccount(user_id=request.user.id, provider=provider,
                                    uid=profile['id'], profile=profile)
            account.save()

            serializer = UserSerializer(request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_profile(self, provider, access_token):
        """
        Request the user's profile from `provider`, and return a dictionary with
        any info the provider gives us.
        """
        if provider == SocialAccount.FACEBOOK:
            profile = self.get_facebook_profile(access_token)

        # Set the access_token on the profile in case we need to re-auth the user.
        profile['access_token'] = access_token

        return profile

    def get_facebook_profile(self, access_token):
        """
        Return a dictionary with the user's Facebook profile.
        """
        params = {'access_token': access_token}
        url = 'https://graph.facebook.com/v2.2/me?' + urlencode(params)
        r = requests.get(url)
        if r.status_code != 200:
            raise ServiceUnavailable(r.content)
        # TODO: Handle bad data.
        profile = r.json()
        profile['image_url'] = ('https://graph.facebook.com/v2.2/{id}/'
                                'picture').format(id=profile['id'])
        return profile


class AuthCodeViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = AuthCode.objects.all()
    serializer_class = AuthCodeSerializer

    def create(self, request, *args, **kwargs):
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
        client.messages.create(to=phone, from_=settings.TWILIO_PHONE, body=message)
    

class SessionView(APIView):

    def post(self, request):
        # TODO: Handle when the data is invalid.
        serializer = SessionSerializer(data=request.data)
        serializer.is_valid()

        try:
            auth = AuthCode.objects.get(phone=serializer.data['phone'], 
                                        code=serializer.data['code'])
        except AuthCode.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # Delete the auth code to keep the db clean
        auth.delete()

        # Get or create the user
        try:
            phone = serializer.data['phone']
            user_number = UserPhoneNumber.objects.get(phone=phone)
            # User exists
            user = user_number.user
        except UserPhoneNumber.DoesNotExist:
            # User doesn't already exist, so create a blank new user and phone
            # number.
            user = User()
            user.save()

            user_number = UserPhoneNumber(user=user, phone=serializer.data['phone'])
            user_number.save()

        token, created = Token.objects.get_or_create(user=user)
        user.authtoken = token.key

        # Generate a Firebase token every time.
        # TODO: Don't set the firebase token on the user. Just add it as
        # extra context to the user serializer.
        #auth_payload = {'uid': unicode(uuid.uuid1())}
        auth_payload = {'uid': unicode(user.id)}
        firebase_token = create_token(settings.FIREBASE_SECRET, auth_payload)
        user.firebase_token = firebase_token

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserPhoneNumberView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """
        Return a list of users with the given phone numbers.

        We're using POST here mainly because the list of phone numbers may not
        be able to fit in the query parameters of a GET request.
        """
        import logging
        logger = logging.getLogger('console')
        logger.info('request data:')
        logger.info(request.data)
        # TODO: Handle when the data is invalid.
        serializer = PhoneSerializer(data=request.data)
        serializer.is_valid()
        logger.info('phone serializer data:')
        logger.info(serializer.data)

        # Filter user phone numbers using the phone number data.
        phones = serializer.data['phones']
        user_phones = UserPhoneNumber.objects.filter(phone__in=phones)
        user_phones.prefetch_related('user')
        logger.info('user phones:')
        logger.info(user_phones)

        serializer = UserPhoneNumberSerializer(user_phones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TermsView(TemplateView):
    template_name = 'terms.html'


class LandingView(TemplateView):
    template_name = 'landing.html'


class LinfootFunnelViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = LinfootFunnel.objects.all()
    serializer_class = LinfootFunnelSerializer


class AppStoreView(RedirectView):
    url = ('https://itunes.apple.com/us/app/down-connect-people-around/id'
           '969040287?mt=8')
    permanent = False
