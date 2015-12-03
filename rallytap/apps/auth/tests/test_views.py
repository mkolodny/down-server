from __future__ import unicode_literals
from binascii import a2b_hex
from datetime import datetime, timedelta
import json
import mock
from urllib import urlencode
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import timezone
import httpretty
import pytz
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APITestCase
import time
from twilio import TwilioRestException
from rallytap.apps.auth.models import (
    AuthCode,
    FellowshipApplication,
    LinfootFunnel,
    Points,
    SocialAccount,
    User,
    UserPhone,
)
from rallytap.apps.auth.serializers import (
    FriendSerializer,
    UserSerializer,
    UserPhoneSerializer,
)
from rallytap.apps.events.models import Event, SavedEvent
from rallytap.apps.events.serializers import (
    SavedEventSerializer,
    SavedEventFullEventSerializer,
)
from rallytap.apps.friends.models import Friendship
from rallytap.apps.utils.exceptions import ServiceUnavailable


class UserTests(APITestCase):

    def setUp(self):
        self.patcher = mock.patch('requests.patch')
        self.mock_patch = self.patcher.start()

        # Mock a user.
        self.user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                         first_name='Alan', last_name='Turing', username='tdog',
                         image_url='http://imgur.com/tdog',
                         location='POINT(50.7545645 -73.9813595)')
        self.user.save()
        self.user_social = SocialAccount(user=self.user,
                                         provider=SocialAccount.FACEBOOK,
                                         uid='10101293050283881',
                                         profile={'access_token': '1234asdf'})
        self.user_social.save()

        # Authorize the requests with the user's token.
        self.token = Token(user=self.user)
        self.token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # Mock one of the user's friends.
        self.friend1 = User(email='jclarke@gmail.com', name='Joan Clarke',
                            first_name='Joan', last_name='Clarke',
                            image_url='http://imgur.com/jcke',
                            location='POINT(40.7545645 -73.9813595)')
        self.friend1.save()
        self.friendship = Friendship(user=self.user, friend=self.friend1)
        self.friendship.save()
        self.friend1_social = SocialAccount(user=self.friend1,
                                            provider=SocialAccount.FACEBOOK,
                                            uid='20101293050283881',
                                            profile={'access_token': '2234asdf'})
        self.friend1_social.save()

        # Mock the users' phone numbers.
        self.friend1_phone = UserPhone(user=self.friend1, phone='+12036227310')
        self.friend1_phone.save()
        self.user_phone = UserPhone(user=self.user, phone='+14388843460')
        self.user_phone.save()

        # Save the user urls.
        self.detail_url = reverse('user-detail', kwargs={'pk': self.user.id})
        self.list_url = reverse('user-list')
        self.me_url = '{list_url}me'.format(list_url=self.list_url)
        self.friends_url = 'https://graph.facebook.com/v2.2/me/friends'

    def tearDown(self):
        self.patcher.stop()

    def test_get(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the user.
        serializer = UserSerializer(self.user)
        json_user = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user)

    def test_get_not_logged_in(self):
        # Remove the user's credentials.
        self.client.credentials()

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_me(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the authenticated user.
        serializer = UserSerializer(self.user)
        json_user = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user)

    def test_put(self):
        new_name = 'Alan'
        data = {
            'email': self.user.email,
            'name': new_name,
            'username': self.user.username,
            'image_url': self.user.image_url,
        }
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should update the user.
        user = User.objects.get(id=self.user.id)
        self.assertEqual(user.name, new_name)

        # It should return the user.
        serializer = UserSerializer(user)
        json_user = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user)

    def test_put_not_current_user(self):
        detail_url = reverse('user-detail', kwargs={'pk': self.friend1.id})
        response = self.client.put(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_username_rallytap(self):
        new_username = 'rallytap'
        data = {
            'email': self.user.email,
            'name': self.user.name,
            'username': new_username,
            'image_url': self.user.image_url,
        }
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_username_taken(self):
        # TODO
        pass

    def test_query_by_ids(self):
        # Mock another user to make sure they're not returned.
        user = User()
        user.save()

        ids = ','.join([unicode(self.user.id)])
        url = self.list_url + '?ids=' + ids
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the users.
        serializer = UserSerializer([self.user], many=True)
        json_users = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_users)

    def test_query_by_username(self):
        url = '{list_url}?username={username}'.format(list_url=self.list_url,
                                                      username=self.user.username)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return a list with the user.
        serializer = UserSerializer([self.user], many=True)
        json_users = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_users)

    def test_query_by_username_upper(self):
        # Username search should be case insensitive.
        username = self.user.username.upper()
        url = '{list_url}?username={username}'.format(list_url=self.list_url,
                                                      username=username)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return a list with the user.
        serializer = UserSerializer([self.user], many=True)
        json_users = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_users)

    def test_get_username_unique(self):
        url = reverse('user-username-detail', kwargs={'username': 'tpain'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_username_taken(self):
        url = reverse('user-username-detail', kwargs={
            'username': self.user.username,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_username_taken_upper(self):
        # Usernames should be unique regardless of case.
        username = self.user.username.upper()
        url = reverse('user-username-detail', kwargs={
            'username': username,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_friends(self):
        url = reverse('user-friends')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return a list of the user's friends.
        serializer = FriendSerializer([self.friend1], many=True)
        json_friends = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_friends)

    @mock.patch('rallytap.apps.auth.views.utils.get_facebook_friends')
    def test_facebook_friends(self, mock_get_facebook_friends):
        # Mock the friends Facebook returns.
        facebook_friends = [self.friend1]
        mock_get_facebook_friends.return_value = facebook_friends

        url = reverse('user-facebook-friends')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should request the user's facebook friends with their social account.
        user_social = SocialAccount.objects.get(user=self.user)
        mock_get_facebook_friends.assert_called_once_with(user_social)

        # It should return a list of the users facebook friends.
        serializer = FriendSerializer(facebook_friends, many=True)
        json_friends = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_friends)

    @mock.patch('rallytap.apps.auth.views.utils.get_facebook_friends')
    def test_facebook_friends_no_social(self, mock_get_facebook_friends):
        # Mock the user having no social account yet.
        self.user_social.delete()

        url = reverse('user-facebook-friends')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_added_me(self):
        # Mock the friend having added the user, but not vice versa.
        self.friendship.delete()
        friendship = Friendship(user=self.friend1, friend=self.user)
        friendship.save()

        url = reverse('user-added-me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return a list of users who added the current user.
        serializer = FriendSerializer([self.friend1], many=True)
        json_added_me = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_added_me)

    def test_saved_events(self):
        # Mock the user being interested in two events.
        event1 = Event(title='bbq in the park', creator=self.user)
        event1.save()
        saved_event1 = SavedEvent(user=self.user, event=event1,
                                  location=self.user.location)
        saved_event1.save()
        nineteen_eighty = datetime(year=1980, month=5, day=21,
                                   tzinfo=pytz.utc)
        event2 = Event(title='see the new star wars', creator=self.user,
                       datetime=nineteen_eighty)
        event2.save()
        saved_event2 = SavedEvent(user=self.user, event=event2,
                                  location=self.user.location)
        saved_event2.save()

        # Mock the user's friend being interested.
        friend_saved_event = SavedEvent(user=self.friend1, event=event1,
                                        location=self.user.location)
        friend_saved_event.save()

        # Mock another person being interested.
        other_dude = User(name='Jazzy Jeff')
        other_dude.save()
        other_dude_saved_event = SavedEvent(event=event1, user=other_dude,
                                            location=self.user.location)
        other_dude_saved_event.save()

        url = reverse('user-saved-events')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return a list of the user's saved events.
        context = {
            'interested_friends': {
                event1.id: [self.friend1],
                event2.id: [],
            },
            'total_num_interested': {
                event1.id: 3,
                event2.id: 1
            },
        }
        # The saved events should be sorted by when they're happening if
        # the event has a date, and by when the event was created if the
        # event doesn't have a date.
        saved_events = [saved_event1, saved_event2]
        serializer = SavedEventFullEventSerializer(saved_events, many=True,
                                                   context=context)
        json_saved_events = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_saved_events)

    @mock.patch('rallytap.apps.auth.views.send_message')
    def test_invite(self, mock_send_message):
        # Use the meteor server's auth token.
        dt = timezone.now()
        meteor_user = User(id=-1, date_joined=dt)
        meteor_user.save()
        token = Token(user=meteor_user)
        token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Save the user's current score to compare to after the request.
        user_points = self.user.points

        url = reverse('user-invite', kwargs={
            'pk': self.user.id,
        })
        event_title = 'Gettin jiggy with it'
        data = {
            'event_title': event_title,
            'to_user': self.friend1.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should notify the friend that the user invited them.
        user_ids = [self.friend1.id]
        message = '{name}: Are you down for "{title}"?'.format(
                name=self.user.name, title=event_title)
        mock_send_message.assert_any_call(user_ids, message)

        # It should give the user points!
        user = User.objects.get(id=self.user.id)
        self.assertEqual(user.points, user_points+Points.SENT_INVITATION)

    def test_invite_not_meteor(self):
        # Don't use the meteor server's auth token.
        url = reverse('user-invite', kwargs={
            'pk': self.user.id,
        })
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SocialAccountTests(APITestCase):
    
    def setUp(self):
        # Mock the user.
        self.user = User()
        self.user.save()
        self.phone = UserPhone(user=self.user, phone='+12036227310')
        self.phone.save()

        # Mock the user's friend.
        self.friend = User(email='jclarke@gmail.com', name='Joan Clarke')
        self.friend.save()
        self.friendship = Friendship(user=self.user, friend=self.friend)
        self.friendship.save()
        self.friend_account = SocialAccount(user=self.friend,
                                            provider=SocialAccount.FACEBOOK,
                                            uid='10101293050283881')
        self.friend_account.save()

        # Authorize the requests with the user's token.
        self.token = Token(user=self.user)
        self.token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # Save URLs.
        self.url = reverse('social-account-login')

        # Save request data.
        self.facebook_token = 'asdf123'
        self.facebook_user_id = '20101293050283881'
        self.fb_profile = {
            'id': self.facebook_user_id,
            'email': 'aturing@gmail.com',
            'name': 'Alan Turing',
            'first_name': 'Alan',
            'last_name': 'Turing',
            'hometown': 'Paddington, London',
            'image_url': 'https://graph.facebook.com/v2.2/{id}/picture'.format(
                    id=self.facebook_user_id),
            'access_token': self.facebook_token,
        }
        self.post_data = {'access_token': self.facebook_token}


    @httpretty.activate
    @mock.patch('rallytap.apps.auth.views.utils.get_facebook_profile')
    @mock.patch('rallytap.apps.auth.views.utils.get_facebook_friends')
    def test_create(self, mock_get_facebook_friends, mock_get_facebook_profile):
        profile = self.fb_profile

        # Mock requesting the user's profile.
        mock_get_facebook_profile.return_value = profile

        # Mock the user's facebook friends.
        friends = User.objects.filter(id=self.friend.id)
        mock_get_facebook_friends.return_value = friends

        response = self.client.post(self.url, self.post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should update the user.
        user = User.objects.get(id=self.user.id, email=profile['email'],
                                name=profile['name'],
                                first_name=profile['first_name'],
                                last_name=profile['last_name'],
                                image_url=profile['image_url'])

        # It should create the user's social account.
        account = SocialAccount.objects.get(user=self.user,
                                            provider=SocialAccount.FACEBOOK,
                                            uid=self.facebook_user_id)
        self.assertEqual(account.profile, self.fb_profile)

        # It should give Facebook the access token.
        mock_get_facebook_profile.assert_called_once_with(self.facebook_token)

        # It should request the user's facebook friends with their social account.
        social_account = SocialAccount.objects.get(user=self.user)
        mock_get_facebook_friends.assert_called_once_with(social_account)

        # It should return the user.
        data = {
            'facebook_friends': friends,
            'friends': friends,
            'authtoken': self.token.key,
        }
        serializer = UserSerializer(user, context=data)
        json_user = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user)

    @mock.patch('rallytap.apps.auth.views.utils.get_facebook_friends')
    def test_create_exists_for_user(self, mock_get_facebook_friends):
        # Mock the user's social account.
        profile = {'access_token': 'old-access-token'}
        account = SocialAccount(user=self.user, provider=SocialAccount.FACEBOOK,
                                uid=self.facebook_user_id, profile=profile)
        account.save()

        # Mock the user's facebook friends.
        facebook_friends = []
        mock_get_facebook_friends.return_value = facebook_friends

        response = self.client.post(self.url, self.post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should update the user's social account.
        account = SocialAccount.objects.get(id=account.id)
        access_token = self.post_data['access_token']
        self.assertEqual(account.profile['access_token'], access_token)

        # It should request the user's facebook friends with their social account.
        social_account = SocialAccount.objects.get(user=self.user)
        mock_get_facebook_friends.assert_called_once_with(social_account)

        # It should return the user.
        data = {
            'facebook_friends': facebook_friends,
            'friends': [self.friend],
            'authtoken': self.token.key,
        }
        serializer = UserSerializer(self.user, context=data)
        json_user = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user)

    @mock.patch('rallytap.apps.auth.views.utils.get_facebook_profile')
    @mock.patch('rallytap.apps.auth.views.utils.get_facebook_friends')
    @mock.patch('rallytap.apps.auth.views.utils.meteor_login')
    def test_create_exists_for_profile(self, mock_meteor_login,
                                       mock_get_facebook_friends,
                                       mock_get_facebook_profile):
        profile = self.fb_profile

        # Mock requesting the user's profile.
        mock_get_facebook_profile.return_value = profile

        # Mock the user's social account.
        account = SocialAccount(user=self.user, provider=SocialAccount.FACEBOOK,
                                uid=self.facebook_user_id, profile=profile)
        account.save()

        # Log in as a different user.
        user = User()
        user.save()
        user_phone = UserPhone(user=user, phone='+19176229626')
        user_phone.save()
        token = Token(user=user)
        token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Mock the user's facebook friends.
        facebook_friends = []
        mock_get_facebook_friends.return_value = facebook_friends

        response = self.client.post(self.url, self.post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should delete the old user.
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(id=user.id)

        # It should update the old user phone.
        UserPhone.objects.get(user=self.user, phone=user_phone.phone)

        # It should authenticate the user on the meteor server.
        mock_meteor_login.assert_called_once_with(self.token)

        # It should return the user.
        data = {
            'facebook_friends': facebook_friends,
            'friends': self.user.friends,
            'authtoken': self.token.key,
        }
        serializer = UserSerializer(self.user, context=data)
        json_user = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user)

    def test_create_not_logged_in(self):
        # Log the user out.
        self.client.credentials()

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthCodeTests(APITestCase):

    def setUp(self):
        # Save re-used data.
        self.phone_number = '+12345678910'

        # Save URLs.
        self.url = reverse('authcode-list')

        # Set the accept header on all requests.
        self.client.credentials(HTTP_ACCEPT='application/json; version=1.0')

    @mock.patch('rallytap.apps.auth.views.TwilioRestClient')
    def test_create(self, mock_TwilioRestClient):
        # Mock the Twilio SMS API.
        mock_client = mock.MagicMock()
        mock_TwilioRestClient.return_value = mock_client

        response = self.client.post(self.url, {'phone': self.phone_number})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # There should be an AuthCode object with the test phone number
        auth = AuthCode.objects.get(phone=self.phone_number)

        # It should init the Twilio client with the proper params.
        mock_TwilioRestClient.assert_called_with(settings.TWILIO_ACCOUNT,
                                                 settings.TWILIO_TOKEN)

        # It should text the user the auth code.
        message = 'Your Rallytap code: {}'.format(auth.code)
        mock_client.messages.create.assert_called_with(to=self.phone_number, 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=message)

    def test_create_invalid(self):
        # use invalid phone number
        invalid_phone_number = '+12'

        response = self.client.post(self.url, {'phone': invalid_phone_number})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('rallytap.apps.auth.views.TwilioRestClient')
    def test_create_already_exists(self, mock_TwilioRestClient):
        # Mock the Twilio SMS API.
        mock_client = mock.MagicMock()
        mock_TwilioRestClient.return_value = mock_client

        auth = AuthCode(phone=self.phone_number)
        auth.save()

        response = self.client.post(self.url, {'phone': self.phone_number})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should init the Twilio client with the proper params.
        mock_TwilioRestClient.assert_called_with(settings.TWILIO_ACCOUNT,
                                                 settings.TWILIO_TOKEN)

        # It should text the user the auth code.
        message = 'Your Rallytap code: {}'.format(auth.code)
        mock_client.messages.create.assert_called_with(to=self.phone_number, 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=message)

    @mock.patch('rallytap.apps.auth.views.TwilioRestClient')
    def test_create_twilio_error(self, mock_TwilioRestClient):
        # Mock the Twilio SMS API to raise an exception.
        mock_client = mock.MagicMock()
        mock_TwilioRestClient.return_value = mock_client
        mock_client.messages.create.side_effect = TwilioRestException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, 'https://www.twilio.com')

        # Mock the user's auth code.
        auth = AuthCode(phone=self.phone_number)
        auth.save()

        response = self.client.post(self.url, {'phone': self.phone_number})
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_create_apple_test_user(self):
        response = self.client.post(self.url, {'phone': '+15555555555'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_no_version(self):
        # Remove the version number for the accept header.
        self.client.credentials(HTTP_ACCEPT='application/json;')

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class SessionTests(APITestCase):

    def setUp(self):
        # Mock data.
        self.access_token = 'asdf1234'
        facebook_id = '10101293050283881'
        self.fb_profile = {
            'id': facebook_id,
            'email': 'aturing@gmail.com',
            'name': 'Alan Turing',
            'first_name': 'Alan',
            'last_name': 'Turing',
            'hometown': 'Paddington, London',
            'image_url': 'https://graph.facebook.com/v2.2/{id}/picture'.format(
                         id=facebook_id),
            'access_token': self.access_token,
        }

        # Mock the teamrallytap user.
        self.teamrallytap_user = User(username='teamrallytap')
        self.teamrallytap_user.save()

        # Save URLs.
        self.list_url = reverse('session-list')
        self.facebook_url = reverse('session-facebook')
        self.teamrallytap_url = reverse('session-teamrallytap')
    
    @mock.patch('rallytap.apps.auth.views.utils.meteor_login')
    def test_create(self, mock_meteor_login):
        # Mock the user's auth code.
        auth = AuthCode(phone='+12345678910')
        auth.save()

        data = {'phone': unicode(auth.phone), 'code': auth.code}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should delete the auth code.
        with self.assertRaises(AuthCode.DoesNotExist):
            AuthCode.objects.get(code=auth.code, phone=auth.phone)

        # It should create a userphone.
        userphone = UserPhone.objects.get(phone=auth.phone)
        user = userphone.user

        # It should create a token.
        token = Token.objects.get(user=user)

        # It should login to the meteor server.
        mock_meteor_login.assert_called_once_with(token)

        # The user should be friends with Team Rallytap.
        Friendship.objects.get(user=user, friend=self.teamrallytap_user)
        Friendship.objects.get(user=self.teamrallytap_user, friend=user)

        # It should return the user.
        data = {'authtoken': token.key, 'friends': user.friends}
        serializer = UserSerializer(user, context=data)
        json_user = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user)

    def test_create_bad_credentials(self):
        # Mock an auth code.
        auth = AuthCode(phone='+12345678910')
        auth.save()

        data = {'phone': unicode(auth.phone), 'code': (auth.code + 'x')}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def mock_user(self, phone='+12345678901'):
        # Mock an already created user
        self.user = User()
        self.user.save()
        self.userphone = UserPhone(user=self.user, phone=phone)
        self.userphone.save()

        self.auth = AuthCode(phone=phone)
        self.auth.save()

    @mock.patch('rallytap.apps.auth.views.utils.meteor_login')
    def test_create_already_created(self, mock_meteor_login):
        self.mock_user()

        data = {'phone': unicode(self.auth.phone), 'code': self.auth.code}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create a token.
        token = Token.objects.get(user=self.user)

        # It should login to the meteor server.
        mock_meteor_login.assert_called_once_with(token)

        # The response should have the same user object
        data = {'authtoken': token.key, 'friends': self.user.friends}
        serializer = UserSerializer(self.user, context=data)
        user_json = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, user_json)

        # The user's auth code should be deleted.
        with self.assertRaises(AuthCode.DoesNotExist):
            AuthCode.objects.get(id=self.auth.id)

    @mock.patch('rallytap.apps.auth.views.utils.meteor_login')
    def test_create_apple_test_user(self, mock_meteor_login):
        # This is the phone number we let the Apple test user log in with.
        phone = '+15555555555'
        self.mock_user(phone)

        data = {'phone': unicode(self.auth.phone), 'code': self.auth.code}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create a token.
        token = Token.objects.get(user=self.user)

        # It should login to the meteor server.
        mock_meteor_login.assert_called_once_with(token)

        # The response should have the same user object
        data = {'authtoken': token.key, 'friends': self.user.friends}
        serializer = UserSerializer(self.user, context=data)
        user_json = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, user_json)

        # The user's auth code should still exist.
        AuthCode.objects.get(id=self.auth.id)

    @mock.patch('rallytap.apps.auth.views.add_members')
    @mock.patch('rallytap.apps.auth.views.utils.meteor_login')
    def test_create_bad_meteor_response(self, mock_meteor_login,
                                        mock_add_members):
        mock_meteor_login.side_effect = ServiceUnavailable('Bad status')

        # Mock the user's auth code.
        auth = AuthCode(phone='+12345678910')
        auth.save()

        data = {'phone': unicode(auth.phone), 'code': auth.code}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

        # It should create a userphone.
        userphone = UserPhone.objects.get(phone=auth.phone)
        user = userphone.user

        # It should create a token.
        token = Token.objects.get(user=user)

        # It should try to login to the meteor server.
        mock_meteor_login.assert_called_once_with(token)

        # The auth code should still exist.
        AuthCode.objects.get(code=auth.code, phone=auth.phone)

    @mock.patch('rallytap.apps.auth.views.utils.get_facebook_profile')
    @mock.patch('rallytap.apps.auth.views.utils.meteor_login')
    def test_facebook_login(self, mock_meteor_login, mock_get_facebook_profile):
        self.mock_user()
        profile = self.fb_profile

        # Mock requesting the user's profile.
        mock_get_facebook_profile.return_value = profile

        data = {'access_token': self.access_token}
        response = self.client.post(self.facebook_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create the user.
        user = User.objects.get(email=profile['email'], name=profile['name'],
                                first_name=profile['first_name'],
                                last_name=profile['last_name'],
                                image_url=profile['image_url'])

        # It should create the user's social account.
        social_account = SocialAccount.objects.get(user=user,
                                                   provider=SocialAccount.FACEBOOK,
                                                   uid=profile['id'])
        self.assertEqual(social_account.profile, profile)

        # It should give Facebook the access token.
        mock_get_facebook_profile.assert_called_once_with(self.access_token)

        # It should create a token.
        token = Token.objects.get(user=user)

        # It should login to the meteor server.
        mock_meteor_login.assert_called_once_with(token)

        # It should return the user.
        context = {'authtoken': token.key, 'friends': user.friends}
        serializer = UserSerializer(user, context=context)
        json_user = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user)

    @mock.patch('rallytap.apps.auth.views.utils.get_facebook_profile')
    @mock.patch('rallytap.apps.auth.views.utils.meteor_login')
    def test_facebook_login_user_exists(self, mock_meteor_login,
                                        mock_get_facebook_profile):
        profile = self.fb_profile

        # Mock the user, the user's auth token, and their social account.
        user = User(email=profile['email'], name=profile['name'],
                    first_name=profile['first_name'],
                    last_name=profile['last_name'],
                    image_url=profile['image_url'])
        user.save()
        token = Token(user=user)
        token.save()
        social_account = SocialAccount(user=user,
                                       provider=SocialAccount.FACEBOOK,
                                       uid=profile['id'])
        social_account.save()

        # Mock requesting the user's profile.
        mock_get_facebook_profile.return_value = profile

        data = {'access_token': profile['access_token']}
        response = self.client.post(self.facebook_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should login to the meteor server.
        mock_meteor_login.assert_called_once_with(token)

        # It should return the user.
        context = {'authtoken': token.key, 'friends': user.friends}
        serializer = UserSerializer(user, context=context)
        json_user = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user)

    @mock.patch('rallytap.apps.auth.views.utils.meteor_login')
    def test_get_teamrallytap(self, mock_meteor_login):
        # Mock the rallytap user's auth token.
        token = Token(user=self.teamrallytap_user)
        token.save()

        # Mock the rallytap user's friend.
        friend = User(username='teamtaprally')
        friend.save()
        friendship = Friendship(user=self.teamrallytap_user, friend=friend)
        friendship.save()

        # Mock a staff member.
        staff_user = User(is_staff=True)
        staff_user.save()
        staff_token = Token(user=staff_user)
        staff_token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + staff_token.key)

        response = self.client.get(self.teamrallytap_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should login to the meteor server.
        mock_meteor_login.assert_called_once_with(token)

        # It should return the rallytap user.
        context = {'authtoken': token.key, 'friends': [friend]}
        serializer = UserSerializer(self.teamrallytap_user, context=context)
        json_user = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user)

    def test_get_teamrallytap_non_staff(self):
        # Mock a non-staff member.
        user = User(is_staff=False)
        user.save()
        token = Token(user=user)
        token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(self.teamrallytap_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserPhoneTests(APITestCase):

    def setUp(self):
        # Mock the user.
        self.user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                         username='tdog', image_url='http://imgur.com/tdog')
        self.user.save()
        self.userphone = UserPhone(user=self.user, phone='+14388843460')
        self.userphone.save()

        # Authorize the requests with the user's token.
        self.token = Token(user=self.user)
        self.token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # Mock the teamrallytap user.
        self.teamrallytap_user = User(username='teamrallytap')
        self.teamrallytap_user.save()

        # Save URLs.
        self.list_url = reverse('userphone-list')
        self.phones_url = reverse('userphone-contacts')

    def test_query_by_contacts(self):
        contact_phone = '+19176227310'
        contact_name = 'Ada Lovelace'

        # Mock a user who was added by phone number.
        phone = '+12038333650'
        added_by_phone_user = User(name=phone)
        added_by_phone_user.save()
        added_by_phone_name = 'Leslie Knope'
        added_by_phone_userphone = UserPhone(user=added_by_phone_user, phone=phone)
        added_by_phone_userphone.save()

        # Mock a user who logged in with their phone number, but hasn't synced
        # with Facebook yet.
        no_name_user = User()
        no_name_user.save()
        no_name_phone = '+15148333650'
        no_name_name = 'Angela Lansbury'
        no_name_userphone = UserPhone(user=no_name_user, phone=no_name_phone)
        no_name_userphone.save()

        data = {'contacts': [
            {
                'name': self.user.name,
                'phone': unicode(self.userphone.phone),
            },
            {
                'name': added_by_phone_name,
                'phone': phone,
            },
            {
                'name': contact_name,
                'phone': contact_phone,
            },
            {
                'name': no_name_name,
                'phone': no_name_phone,
            },
        ]}
        response = self.client.post(self.phones_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should create a userphone for the extra phone number.
        contact_userphone = UserPhone.objects.get(phone=contact_phone)

        # It should name the contact.
        contact_user = contact_userphone.user
        self.assertEqual(contact_user.name, contact_name)

        # It should make the contact friends with Team Rallytap.
        Friendship.objects.get(user=contact_user, friend=self.teamrallytap_user)
        Friendship.objects.get(user=self.teamrallytap_user, friend=contact_user)

        # It should update the user who was added by phone number's name.
        user = User.objects.get(id=added_by_phone_user.id)
        self.assertEqual(user.name, added_by_phone_name)

        # It should update the user who didn't have a name's name.
        user = User.objects.get(id=no_name_user.id)
        self.assertEqual(user.name, no_name_name)

        # It should return a list with the userphones.
        added_by_phone_userphone = UserPhone.objects.get(
                id=added_by_phone_userphone.id)
        no_name_userphone = UserPhone.objects.get(
                id=no_name_userphone.id)
        userphones = [
            self.userphone,
            added_by_phone_userphone,
            no_name_userphone,
            contact_userphone,
        ]
        serializer = UserPhoneSerializer(userphones, many=True)
        json_user_phones = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user_phones)

    def test_query_by_contacts_not_logged_in(self):
        # Unauth the user.
        self.client.credentials()

        response = self.client.post(self.phones_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create(self):
        data = {'phone': '+19178699626'}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create a userphone with the given number.
        userphone = UserPhone.objects.get(**data)

        # It should set the user's name to their phone number.
        user = userphone.user
        self.assertEqual(user.name, data['phone'])

        # The user should be friends with Team Rallytap.
        Friendship.objects.get(user=user, friend=self.teamrallytap_user)
        Friendship.objects.get(user=self.teamrallytap_user, friend=user)

        # It should return the userphone.
        serializer = UserPhoneSerializer(userphone)
        json_user_phone = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user_phone)

    def test_create_already_exists(self):
        data = {'phone': unicode(self.userphone.phone)}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should return the userphone.
        serializer = UserPhoneSerializer(self.userphone)
        json_user_phone = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user_phone)


class LinfootFunnelTests(APITestCase):

    def test_create(self):
        url = reverse('phonenumbers-list')
        data = {'phone': '+12036227310'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create a linfoot funnel.
        LinfootFunnel.objects.get(**data)

    def test_create_already_exists(self):
        phone = '+12036227310'
        funnel = LinfootFunnel(phone=phone)
        funnel.save()

        url = reverse('phonenumbers-list')
        data = {'phone': phone}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class FellowshipApplicationTests(APITestCase):

    def setUp(self):
        self.list_url = reverse('fellowship-application-list')
        self.post_data = {
            'username': 'r',
            'school': 'Stuyvesant High School',
        }

    def test_create(self):
        data = self.post_data
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create a fellowship application.
        FellowshipApplication.objects.get(username=data['username'],
                                          school=data['school'])
