from __future__ import unicode_literals
from binascii import a2b_hex
from datetime import datetime, timedelta
import json
import mock
from urllib import urlencode
from django.conf import settings
from django.core.urlresolvers import reverse
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
from down.apps.auth.serializers import UserSerializer, UserPhoneSerializer
from down.apps.events.models import AllFriendsInvitation, Event, Invitation
from down.apps.events.serializers import EventSerializer
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
        self.invited_events_url = reverse('user-invited-events',
                                          kwargs={'pk': self.user.id})

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
        url = reverse('user-friends', kwargs={'pk': self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return a list of the user's friends.
        serializer = UserSerializer([self.friend1], many=True)
        json_friends = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_friends)

    def test_invited_events(self):
        # Create an new event with an open invitation.
        event = Event(creator=self.friend1, title='Ex Machina')
        event.save()
        all_friends_invitation = AllFriendsInvitation(from_user=self.friend1,
                                                      event=event)
        all_friends_invitation.save()

        # Have the friend add the user as their friend.
        friendship = Friendship(user=self.friend1, friend=self.user)
        friendship.save()

        # Set the user to be within 5 miles of the friend.
        self.user.location = 'POINT(40.685339 -73.979361)'
        self.user.save()

        response = self.client.get(self.invited_events_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return a list of the events that the user was invited to.
        serializer = EventSerializer([self.event, event], many=True)
        json_events = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_events)

    @mock.patch('django.db.models.fields.timezone.now')
    def test_invited_events_min_updated_at(self, mock_now):
        # Set the event to having been updated a significant amount later than
        # the first event. Since `auto_now` sets the value of `updated_at` using
        # `timezone.now()`, mock `timezone.now()` to return the time one minute
        # after the current time.
        dt = datetime.now().replace(tzinfo=pytz.utc) + timedelta(minutes=1)
        mock_now.return_value = dt

        # Mock another event that the user's invited to.
        event = Event(title='rat fishing', creator=self.friend1)
        event.save()
        invitation = Invitation(from_user=self.friend1, to_user=self.user,
                                event=event)
        invitation.save()

        updated_at = int(time.mktime(event.updated_at.timetuple()))
        self.invited_events_url += '?min_updated_at=' + unicode(updated_at)
        response = self.client.get(self.invited_events_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return a list of the user's invitations that have been updated
        # since `min_updated_at`.
        serializer = EventSerializer([event], many=True)
        json_events = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_events)

    @mock.patch('django.db.models.fields.timezone.now')
    def test_invited_events_invitation_updated(self, mock_now):
        # Set the invitation to having been updated a significant amount later than
        # the event. Since `auto_now` sets the value of `updated_at` using
        # `timezone.now()`, mock `timezone.now()` to return the time one minute
        # after the current time.
        dt = datetime.now().replace(tzinfo=pytz.utc) + timedelta(minutes=1)
        mock_now.return_value = dt

        # Update the invitation.
        self.friend1_invitation.response = Invitation.DECLINED
        self.friend1_invitation.save()

        timetuple = self.friend1_invitation.updated_at.timetuple()
        updated_at = int(time.mktime(timetuple))
        self.invited_events_url += '?min_updated_at=' + unicode(updated_at)
        response = self.client.get(self.invited_events_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return a list of the user's invitations that have been updated
        # since `min_updated_at`.
        event = Event.objects.get(id=self.event.id)
        serializer = EventSerializer([event], many=True)
        json_events = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_events)

    @httpretty.activate
    def test_facebook_friends(self):
        # Mock the user's facebook friends.
        body = json.dumps({
            'data': [{
                'name': 'Joan Clarke', 
                'id': self.friend1_social.uid,
            }],
            'paging': {
            },
        })
        httpretty.register_uri(httpretty.GET, self.friends_url, body=body,
                               content_type='application/json')
        
        url = reverse('user-facebook-friends', kwargs={'pk': self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should request the user's friends with their facebook access token.
        querystring = {'access_token': [self.user_social.profile['access_token']]}
        self.assertEqual(httpretty.last_request().querystring, querystring)

        # It should return a list of the users facebook friends.
        serializer = UserSerializer([self.friend1], many=True)
        json_friends = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_friends)

    @httpretty.activate
    def test_facebook_friends_next_page(self):
        # Mock another of the user's friends.
        friend = User(email='htubman@gmail.com', name='Harriet Tubman',
                      image_url='http://imgur.com/tubby')
        friend.save()
        friendship = Friendship(user=self.user, friend=friend)
        friendship.save()
        friend_social = SocialAccount(user=friend,
                                      provider=SocialAccount.FACEBOOK,
                                      uid='30101293050283881',
                                      profile={'access_token': '3234asdf'})
        friend_social.save()

        # Mock the user having more than 25 friends on Down.
        next_url = 'https://graph.facebook.com/v2.2/123/friends'
        body = json.dumps({
            'data': [{
                'name': 'Joan Clarke', 
                'id': self.friend1_social.uid,
            } for i in xrange(25)],
            'paging': {
                'next': next_url,
            },
        })
        httpretty.register_uri(httpretty.GET, self.friends_url, body=body,
                               content_type='application/json')

        # Mock the next url response.
        body = json.dumps({
            'data': [{
                'name': 'Joan Clarke', 
                'id': friend_social.uid,
            }],
            'paging': {
            }
        })
        httpretty.register_uri(httpretty.GET, next_url, body=body,
                               content_type='application/json')
        
        url = reverse('user-facebook-friends', kwargs={'pk': self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return a list of the users facebook friends.
        serializer = UserSerializer([self.friend1, friend], many=True)
        json_friends = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_friends)

    @httpretty.activate
    def test_facebook_friends_bad_response(self):
        # Mock a bad response from Facebook when requesting the user's facebook
        # friends.
        httpretty.register_uri(httpretty.GET, self.friends_url,
                               status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        url = reverse('user-facebook-friends', kwargs={'pk': self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @httpretty.activate
    def test_facebook_friends_no_content(self):
        # Mock bad response data from Facebook when requesting the user's facebook
        # friends.
        httpretty.register_uri(httpretty.GET, self.friends_url, body='',
                               status=status.HTTP_200_OK)
        
        url = reverse('user-facebook-friends', kwargs={'pk': self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @httpretty.activate
    def test_facebook_friends_no_data(self):
        # Mock Facebook response data without a `data` property.
        httpretty.register_uri(httpretty.GET, self.friends_url, body=json.dumps({}),
                               status=status.HTTP_200_OK)
        
        url = reverse('user-facebook-friends', kwargs={'pk': self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)


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
        self.name = 'Alan Tdog Turing'
        self.image_url = 'https://graph.facebook.com/v2.2/{id}/picture'.format(
                id=self.facebook_user_id)
        self.hometown = 'Paddington, London'
        self.post_data = {'access_token': self.facebook_token}

    @httpretty.activate
    def test_create(self):
        # Request the user's profile.
        body = json.dumps({
            'id': self.facebook_user_id,
            'email': self.email,
            'name': self.name,
            'hometown': self.hometown,
        })
        httpretty.register_uri(httpretty.GET, self.profile_url, body=body,
                               content_type='application/json')

        response = self.client.post(self.url, self.post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should update the user.
        user = User.objects.get(id=self.user.id, email=self.email,
                                name=self.name, image_url=self.image_url)

        # It should create the user's social account.
        profile = {
            'access_token': self.facebook_token,
            'id': self.facebook_user_id,
            'email': self.email,
            'name': self.name,
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

        # It should return the user.
        serializer = UserSerializer(user)
        json_user = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user)

    @httpretty.activate
    def test_create_no_email(self):
        # Request the user's profile.
        body = json.dumps({
            'id': self.facebook_user_id,
            'name': self.name,
            'hometown': self.hometown,
        })
        httpretty.register_uri(httpretty.GET, self.profile_url, body=body,
                               content_type='application/json')

        response = self.client.post(self.url, self.post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should update the user with a default email.
        default_email = 'no.email@down.life'
        user = User.objects.get(id=self.user.id, name=self.name,
                                email=default_email, image_url=self.image_url)

        # It should create the user's social account.
        profile = {
            'access_token': self.facebook_token,
            'id': self.facebook_user_id,
            'name': self.name,
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

        # It should return the user.
        serializer = UserSerializer(user)
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
    
    @mock.patch('down.apps.auth.views.create_token')
    def test_create(self, mock_create_token):
        # Make sure no users have been created yet
        self.assertEquals(User.objects.count(), 0)

        # Generate a Firebase token.
        firebase_token = 'qwer1234'
        mock_create_token.return_value = firebase_token

        # Mock the user's auth code.
        auth = AuthCode(phone='+12345678910')
        auth.save()

        url = reverse('session')
        data = {'phone': unicode(auth.phone), 'code': auth.code}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should delete the auth code
        with self.assertRaises(AuthCode.DoesNotExist):
            AuthCode.objects.get(code=auth.code, phone=auth.phone)

        # Make sure we've created a user for this number 
        user = User.objects.get()

        # Make sure the phone number was created
        UserPhone.objects.get(user=user, phone=auth.phone)

        # Get the token, which should've been created
        token = Token.objects.get(user=user)

        # It should generate a Firebase token.
        auth_payload = {'uid': unicode(user.id)}
        mock_create_token.assert_called_with(settings.FIREBASE_SECRET, auth_payload)

        # Check that the response is the user we're expecting
        user.authtoken = token.key
        user.firebase_token = firebase_token
        serializer = UserSerializer(user)
        json_user = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user)

    def test_create_bad_credentials(self):
        # Mock an auth code.
        auth = AuthCode(phone='+12345678910')
        auth.save()

        url = reverse('session')
        data = {'phone': unicode(auth.phone), 'code': (auth.code + 'x')}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @mock.patch('down.apps.auth.views.create_token')
    @mock.patch('down.apps.auth.views.uuid')
    def create_already_created(self, phone_number, mock_uuid, mock_create_token):
        firebase_uuid = 9876
        firebase_token = 'qwer1234'
        mock_uuid.uuid1.return_value = firebase_uuid
        mock_create_token.return_value = firebase_token

        # Mock an already created user
        mock_user = User()
        mock_user.save()

        mock_user_number = UserPhone(user=mock_user, phone=phone_number)
        mock_user_number.save()

        # User has already logged in, so mock their token
        token = Token(user=mock_user)
        token.save()

        url = reverse('session')
        self.auth = AuthCode(phone=phone_number)
        self.auth.save()

        data = {'phone': unicode(self.auth.phone), 'code': self.auth.code}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        mock_user.authtoken = token.key
        mock_user.firebase_token = firebase_token
        serializer = UserSerializer(mock_user)
        mock_user_json = JSONRenderer().render(serializer.data)

        # Response should have the same user object
        user_json = response.content
        self.assertEqual(user_json, mock_user_json)

        # The number of users in the database should still be 1
        self.assertEqual(User.objects.count(), 1)

    def test_create_already_created(self):
        phone_number = '+12345678910'
        self.create_already_created(phone_number)

    def test_create_apple_test_user(self):
        phone_number = '+15555555555'
        self.create_already_created(phone_number)

        # The user's auth code should still exist.
        AuthCode.objects.get(id=self.auth.id)


class UserPhoneViewSetTests(APITestCase):

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

    def test_get(self):
        url = reverse('landing')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'landing.html')


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
