from __future__ import unicode_literals
from django.conf import settings
from django.contrib import auth
from urllib import urlencode
from firebase_token_generator import create_token
import requests
from rest_framework import status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.filters import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import SocialAccount, User
from .serializers import SocialAccountLoginSerializer, UserSerializer
from down.apps.auth.filters import UserFilter
from down.apps.events.models import Invitation
from down.apps.events.serializers import EventSerializer
from down.apps.friends.models import Friendship


# TODO: Security
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_class = UserFilter

    @detail_route(methods=['get'])
    def friends(self, request, pk=None):
        # TODO: Handle when the user doesn't exist.
        user = User.objects.get(id=pk)
        serializer = UserSerializer(user.friends, many=True)
        return Response(serializer.data)

    @detail_route(methods=['get'])
    def invited_events(self, request, pk=None, url_path='invited-events'):
        # TODO: Handle when the user doesn't exist.
        user = User.objects.get(id=pk)
        invitations = Invitation.objects.filter(to_user=user)
        events = [invitation.event for invitation in invitations]
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)


class UserUsernameDetail(APIView):

    def get(self, request, username=None):
        try:
            User.objects.get(username=username)
            return Response()
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class SocialAccountLogin(APIView):

    def post(self, request):
        serializer = SocialAccountLoginSerializer(data=request.data)
        # TODO: Handle when the data is invalid.
        serializer.is_valid()

        # Request the user's profile from the selected provider.
        provider = serializer.data['provider']
        access_token = serializer.data['access_token']
        profile = self.get_profile(provider, access_token)

        # Check whether the user is already signed up.
        try:
            account = SocialAccount.objects.get(uid=profile['id'])
            user = account.user
            status_code = status.HTTP_200_OK
        except SocialAccount.DoesNotExist:
            # Create a new user.
            user = User(email=profile['email'], name=profile['name'],
                        image_url=profile['image_url'])
            user.save()

            # Create the user's social account.
            account = SocialAccount(user_id=user.id, provider=provider,
                                    uid=profile['id'], profile=profile)
            account.save()

            self.save_friends(provider, access_token, user)
            status_code = status.HTTP_201_CREATED

        # Facebook is handling auth for us right now, so we just pass the user
        # to authenticate to set the backend.
        auth.authenticate(user=user)
        auth.login(request, user)

        # Generate a Firebase token.
        auth_payload = {'uid': user.id}
        firebase_token = create_token(settings.FIREBASE_SECRET, auth_payload)

        # TODO: Don't set the firebase token on the user. Just add it as
        # extra context to the user serializer.
        user.firebase_token = firebase_token

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status_code)

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
        profile = self.get_facebook_data(url)
        profile['image_url'] = ('https://graph.facebook.com/v2.2/{id}/'
                'picture').format(id=profile['id'])
        return profile

    def save_friends(self, provider, access_token, user):
        """
        Get the user's friends on `provider`, and save them as the user's friends.

        TODO: Let user's befriend only the people they want to be friends with on
        down.
        """
        if provider == SocialAccount.FACEBOOK:
            self.save_facebook_friends(access_token, user)

    def save_facebook_friends(self, access_token, user):
        """
        Save the user's Facebook friends as down friends.
        """
        params = {'access_token': access_token}
        url = 'https://graph.facebook.com/v2.2/me/friends?' + urlencode(params)
        friends = self.get_facebook_data(url)
        friendships = []
        for friend in friends:
            # TODO: Think about saving the social account uid on the user to avoid
            # retrieving the social account.
            account = SocialAccount.objects.get(uid=friend['id'])
            friendship = Friendship(user1_id=user.id, user2_id=account.user_id)
            friendships.append(friendship)
        Friendship.objects.bulk_create(friendships)

    def get_facebook_data(self, url):
        """
        Request data from Facebook, and return the data as a dictionary.
        """
        r = requests.get(url)
        # TODO: Handle request errors.
        json = r.json()
        # TODO: Handle bad data.
        return json['data']
