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
from down.apps.auth.models import (
    AuthCode,
    LinfootFunnel,
    SocialAccount,
    User,
    UserPhone,
)
from down.apps.auth.serializers import (
    FriendSerializer,
    UserSerializer,
    UserPhoneSerializer,
)
from down.apps.events.models import Event, Invitation
from down.apps.events.serializers import (
    EventSerializer,
    InvitationSerializer,
    MyInvitationSerializer,
)
from down.apps.friends.models import Friendship


class UserTests(APITestCase):

    # We have to mock the function that sends push notifications, since adding
    # mock friends will send push notifications.
    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def setUp(self, mock_send):
        self.patcher = mock.patch('requests.patch')
        self.mock_patch = self.patcher.start()

        # Mock a user.
        self.user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                         username='tdog', image_url='http://imgur.com/tdog',
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

        # Mock two of the user's friends.
        self.friend1 = User(email='jclarke@gmail.com', name='Joan Clarke',
                            image_url='http://imgur.com/jcke',
                            location='POINT(40.7545645 -73.9813595)')
        self.friend1.save()
        friendship = Friendship(user=self.user, friend=self.friend1)
        friendship.save()
        self.friend1_social = SocialAccount(user=self.friend1,
                                            provider=SocialAccount.FACEBOOK,
                                            uid='20101293050283881',
                                            profile={'access_token': '2234asdf'})
        self.friend1_social.save()

        # Mock an event that the user's invited to.
        self.event = Event(title='bars?!?!?!', creator=self.friend1)
        self.event.save()
        self.user_invitation = Invitation(from_user=self.friend1, to_user=self.user,
                                          event=self.event)
        self.user_invitation.save()
        self.friend1_invitation = Invitation(from_user=self.friend1,
                                             to_user=self.friend1, event=self.event)
        self.friend1_invitation.save()

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
        self.invitations_url = reverse('user-invitations')

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

    def test_query_by_ids(self):
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

    def test_get_invitations(self):
        response = self.client.get(self.invitations_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the active invitations.
        serializer = MyInvitationSerializer([self.user_invitation], many=True)
        json_invitations = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_invitations)

    def test_get_invitations_created_expired(self):
        # Mock an expired event without a datetime (by default, events expire after
        # 24 hours).
        self.event.created_at = timezone.now() - timedelta(hours=24)
        self.event.save()

        # Mock not-expired event without a datetime.
        event = Event(title='Beach Day', creator=self.user)
        event.save()
        invitation = Invitation(event=event, from_user=self.user, to_user=self.user)
        invitation.save()

        response = self.client.get(self.invitations_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should only return the active invitations.
        serializer = MyInvitationSerializer([invitation], many=True)
        json_invitations = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_invitations)

    def test_get_invitations_datetime_expired(self):
        # Mock an expired event with a datetime (by default, events expire 24 hours
        # after the end of the event).
        self.event.datetime = timezone.now() - timedelta(hours=24)
        self.event.save()

        # Mock not-expired event with a datetime.
        tomorrow = timezone.now() + timedelta(hours=24)
        event = Event(title='Beach Day', creator=self.user, datetime=tomorrow)
        event.save()
        invitation = Invitation(event=event, from_user=self.user, to_user=self.user)
        invitation.save()

        response = self.client.get(self.invitations_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should only return the active invitations.
        serializer = MyInvitationSerializer([invitation], many=True)
        json_invitations = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_invitations)

    @mock.patch('down.apps.auth.views.get_facebook_friends')
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

    @mock.patch('down.apps.auth.views.get_facebook_friends')
    def test_facebook_friends_no_social(self, mock_get_facebook_friends):
        # Mock the user having no social account yet.
        self.user_social.delete()

        url = reverse('user-facebook-friends')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


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
        self.profile_url = 'https://graph.facebook.com/v2.2/me'

        # Save request data.
        self.facebook_token = 'asdf123'
        self.facebook_user_id = 1207059
        self.email = 'aturing@gmail.com'
        self.name = 'Alan Turing'
        self.first_name = 'Alan'
        self.last_name = 'Turing'
        self.image_url = 'https://graph.facebook.com/v2.2/{id}/picture'.format(
                id=self.facebook_user_id)
        self.hometown = 'Paddington, London'
        self.post_data = {'access_token': self.facebook_token}

    @httpretty.activate
    @mock.patch('down.apps.auth.views.get_facebook_friends')
    def test_create(self, mock_get_facebook_friends):
        # Mock requesting the user's profile.
        body = json.dumps({
            'id': self.facebook_user_id,
            'email': self.email,
            'name': self.name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'hometown': self.hometown,
        })
        httpretty.register_uri(httpretty.GET, self.profile_url, body=body,
                               content_type='application/json')

        # Mock the user's facebook friends.
        facebook_friends = User.objects.filter(id=self.friend.id)
        mock_get_facebook_friends.return_value = facebook_friends

        response = self.client.post(self.url, self.post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should update the user.
        user = User.objects.get(id=self.user.id, email=self.email,
                                name=self.name, first_name=self.first_name,
                                last_name=self.last_name,
                                image_url=self.image_url)

        # It should create the user's social account.
        profile = {
            'access_token': self.facebook_token,
            'id': self.facebook_user_id,
            'email': self.email,
            'name': self.name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'image_url': self.image_url,
            'hometown': self.hometown,
        }
        account = SocialAccount.objects.get(user=self.user,
                                            provider=SocialAccount.FACEBOOK,
                                            uid=self.facebook_user_id)
        self.assertEqual(account.profile, profile)

        # It should give Facebook the access token.
        params = {'access_token': [self.facebook_token]}
        self.assertEqual(httpretty.last_request().querystring, params)

        # It should request the user's facebook friends with their social account.
        social_account = SocialAccount.objects.get(user=self.user)
        mock_get_facebook_friends.assert_called_once_with(social_account)

        # It should return the user.
        data = {'facebook_friends': facebook_friends}
        serializer = UserSerializer(user, context=data)
        json_user = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user)

    @httpretty.activate
    @mock.patch('down.apps.auth.views.get_facebook_friends')
    def test_create_no_email(self, mock_get_facebook_friends):
        # Request the user's profile.
        body = json.dumps({
            'id': self.facebook_user_id,
            'name': self.name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'hometown': self.hometown,
        })
        httpretty.register_uri(httpretty.GET, self.profile_url, body=body,
                               content_type='application/json')

        # Mock the user's facebook friends.
        facebook_friends = []
        mock_get_facebook_friends.return_value = facebook_friends

        response = self.client.post(self.url, self.post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should update the user with a default email.
        default_email = 'no.email@down.life'
        user = User.objects.get(id=self.user.id, name=self.name,
                                email=default_email, first_name=self.first_name,
                                last_name=self.last_name,
                                image_url=self.image_url)

        # It should create the user's social account.
        profile = {
            'access_token': self.facebook_token,
            'id': self.facebook_user_id,
            'name': self.name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'image_url': self.image_url,
            'hometown': self.hometown,
        }
        account = SocialAccount.objects.get(user=self.user,
                                            provider=SocialAccount.FACEBOOK,
                                            uid=self.facebook_user_id)
        self.assertEqual(account.profile, profile)

        # It should give Facebook the access token.
        params = {'access_token': [self.facebook_token]}
        self.assertEqual(httpretty.last_request().querystring, params)

        # It should request the user's facebook friends with their social account.
        social_account = SocialAccount.objects.get(user=self.user)
        mock_get_facebook_friends.assert_called_once_with(social_account)

        # It should return the user.
        data = {'facebook_friends': facebook_friends}
        serializer = UserSerializer(user, context=data)
        json_user = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user)

    @mock.patch('down.apps.auth.views.get_facebook_friends')
    def test_create_already_exists(self, mock_get_facebook_friends):
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
        data = {'facebook_friends': facebook_friends}
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

    @mock.patch('down.apps.auth.views.TwilioRestClient')
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
        message = 'Your Down code: {}'.format(auth.code)
        mock_client.messages.create.assert_called_with(to=self.phone_number, 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=message)

    def test_create_invalid(self):
        # use invalid phone number
        invalid_phone_number = '+12'

        response = self.client.post(self.url, {'phone': invalid_phone_number})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('down.apps.auth.views.TwilioRestClient')
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
        message = 'Your Down code: {}'.format(auth.code)
        mock_client.messages.create.assert_called_with(to=self.phone_number, 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=message)

    @mock.patch('down.apps.auth.views.TwilioRestClient')
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
        # Save URLs.
        self.list_url = reverse('session')
        self.meteor_url = '{meteor_url}/users'.format(
                meteor_url=settings.METEOR_URL)

        # Mock a successfuly meteor server response.
        httpretty.enable()
        httpretty.register_uri(httpretty.POST, self.meteor_url,
                               content_type='application/json')

    def tearDown(self):
        httpretty.disable()
    
    def test_create(self):
        # Make sure no users have been created yet.
        self.assertEquals(User.objects.count(), 0)

        # Mock the user's auth code.
        auth = AuthCode(phone='+12345678910')
        auth.save()

        data = {'phone': unicode(auth.phone), 'code': auth.code}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should delete the auth code.
        with self.assertRaises(AuthCode.DoesNotExist):
            AuthCode.objects.get(code=auth.code, phone=auth.phone)

        # It should create a user associated with the given number.
        user = User.objects.get()

        # It should create a userphone.
        UserPhone.objects.get(user=user, phone=auth.phone)

        # It should create a token.
        token = Token.objects.get(user=user)

        # It should authenticate the user on the meteor server.
        self.assertEqual(httpretty.last_request().body, json.dumps({
            'user_id': user.id,
            'password': token.key,
        }))
        auth_header = 'Token {api_key}'.format(api_key=settings.METEOR_KEY)
        self.assertEqual(httpretty.last_request().headers['Authorization'],
                         auth_header)
        self.assertEqual(httpretty.last_request().headers['Content-Type'],
                         'application/json')

        # It should return the user.
        data = {'authtoken': token.key}
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

    def test_create_already_created(self):
        self.mock_user()

        data = {'phone': unicode(self.auth.phone), 'code': self.auth.code}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create a token.
        token = Token.objects.get(user=self.user)

        # The response should have the same user object
        data = {'authtoken': token.key}
        serializer = UserSerializer(self.user, context=data)
        user_json = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, user_json)

        # The number of users in the database should still be 1
        self.assertEqual(User.objects.count(), 1)

        # The user's auth code should be deleted.
        with self.assertRaises(AuthCode.DoesNotExist):
            AuthCode.objects.get(id=self.auth.id)

    def test_create_apple_test_user(self):
        # This is the phone number we let the Apple test user log in with.
        phone = '+15555555555'
        self.mock_user(phone)

        data = {'phone': unicode(self.auth.phone), 'code': self.auth.code}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create a token.
        token = Token.objects.get(user=self.user)

        # The response should have the same user object
        data = {'authtoken': token.key}
        serializer = UserSerializer(self.user, context=data)
        user_json = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, user_json)

        # The number of users in the database should still be 1
        self.assertEqual(User.objects.count(), 1)

        # The user's auth code should still exist.
        AuthCode.objects.get(id=self.auth.id)

    @httpretty.activate
    def test_create_bad_meteor_response(self):
        # Mock the meteor server response.
        httpretty.register_uri(httpretty.POST, self.meteor_url,
                               content_type='application/json',
                               status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Mock the user's auth code.
        auth = AuthCode(phone='+12345678910')
        auth.save()

        data = {'phone': unicode(auth.phone), 'code': auth.code}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

        # The auth code should still exist.
        AuthCode.objects.get(code=auth.code, phone=auth.phone)


class UserPhoneTests(APITestCase):

    def setUp(self):
        # Mock two users.
        self.user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                         username='tdog', image_url='http://imgur.com/tdog')
        self.user.save()
        self.friend = User(email='jclarke@gmail.com', name='Joan Clarke',
                           image_url='http://imgur.com/jcke')
        self.friend.save()

        # Mock the users' phone numbers.
        self.friend_phone = UserPhone(user=self.friend, phone='+12036227310')
        self.friend_phone.save()
        self.user_phone = UserPhone(user=self.user, phone='+14388843460')
        self.user_phone.save()

        # Authorize the requests with the user's token.
        self.token = Token(user=self.user)
        self.token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # Save URLs.
        self.list_url = reverse('userphone-list')
        self.phones_url = reverse('userphone-phones')
        self.contact_url = reverse('userphone-contact')

    def test_query_by_phones(self):
        # Mock a third user.
        friend = User(email='blee@gmail.com', name='Bruce Lee',
                      username='blee', image_url='http://imgur.com/blee')
        friend.save()
        friend_phone = UserPhone(user=friend, phone='+19176227310')
        friend_phone.save()

        data = {'phones': [
            unicode(self.user_phone.phone),
            unicode(friend_phone.phone),
        ]}
        response = self.client.post(self.phones_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return a list with the userphones.
        userphones = [self.user_phone, friend_phone]
        serializer = UserPhoneSerializer(userphones, many=True)
        json_user_phones = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user_phones)

    def test_query_by_phones_not_logged_in(self):
        # Unauth the user.
        self.client.credentials()

        response = self.client.post(self.phones_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create(self):
        # Save the number of users so far.
        num_users = User.objects.count()

        data = {'phone': '+19178699626'}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create a userphone with the given number.
        UserPhone.objects.get(**data)

        # It should create a new user.
        self.assertEqual(User.objects.count(), num_users+1)

    @mock.patch('down.apps.auth.views.TwilioRestClient')
    def test_create_for_contact(self, mock_twilio):
        # Mock the Twilio SMS API.
        mock_client = mock.MagicMock()
        mock_twilio.return_value = mock_client

        data = {
            'phone': '+19178699626',
            'name': 'Dickface Killah',
        }
        response = self.client.post(self.contact_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create a userphone with the given number.
        UserPhone.objects.get(phone=data['phone'])

        # It should create a new user with the POSTed name.
        User.objects.get(name=data['name'])

        # It should init the Twilio client with the proper params.
        mock_twilio.assert_called_with(settings.TWILIO_ACCOUNT,
                                       settings.TWILIO_TOKEN)

        # It should text the contact.
        message = ('{name} (@{username}) added you as a friend on Down!'
                   ' - http://down.life/app').format(name=self.user.name,
                                                     username=self.user.username)
        mock_client.messages.create.assert_called_with(to=data['phone'], 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=message)

    @mock.patch('down.apps.auth.views.TwilioRestClient')
    def test_create_for_contact_user_exists(self, mock_twilio):
        # Create a user with a name and phone.
        user = User(name='Denise Tinder')
        user.save()
        user_phone = UserPhone(user=user, phone='+19178699626')
        user_phone.save()

        # Mock the Twilio SMS API.
        mock_client = mock.MagicMock()
        mock_twilio.return_value = mock_client

        data = {
            'phone': unicode(user_phone.phone),
            'name': user.name,
        }
        response = self.client.post(self.contact_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should init the Twilio client with the proper params.
        mock_twilio.assert_called_with(settings.TWILIO_ACCOUNT,
                                       settings.TWILIO_TOKEN)

        # It should text the contact.
        message = ('{name} (@{username}) added you as a friend on Down!'
                   ' - http://down.life/app').format(name=self.user.name,
                                                     username=self.user.username)
        mock_client.messages.create.assert_called_with(to=data['phone'], 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=message)

        # It should return the userphone.
        serializer = UserPhoneSerializer(user_phone)
        json_user_phone = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user_phone)


class TermsTests(APITestCase):

    def test_get(self):
        url = reverse('terms')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'terms.html')


class LandingTests(APITestCase):

    """
    def test_get(self):
        url = reverse('landing')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'landing.html')
    """

    def test_redirect(self):
        url = reverse('landing')
        response = self.client.get(url)
        app_store_url = ('https://itunes.apple.com/us/app/down-connect-people'
                         '-around/id969040287?mt=8')
        self.assertRedirects(response, app_store_url,
                             fetch_redirect_response=False)

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


class AppStoreTests(APITestCase):

    def test_redirect(self):
        url = reverse('app-store')
        response = self.client.get(url)
        app_store_url = ('https://itunes.apple.com/us/app/down-connect-people'
                         '-around/id969040287?mt=8')
        self.assertRedirects(response, app_store_url,
                             fetch_redirect_response=False)


class ArticleTests(APITestCase):

    def test_get(self):
        url = reverse('article')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'festivals.html')


class FellowshipFoundersTests(APITestCase):

    def test_get(self):
        url = reverse('founders')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'founders.html')


class FellowshipDemoTests(APITestCase):

    def test_get(self):
        url = reverse('demo')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'demo.html')
