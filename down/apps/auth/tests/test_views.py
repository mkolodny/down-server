from __future__ import unicode_literals
from binascii import a2b_hex
import json
import mock
from urllib import urlencode
from django.conf import settings
from django.core.urlresolvers import reverse
import httpretty
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APITestCase
from down.apps.auth.models import (
    AuthCode,
    LinfootFunnel,
    SocialAccount,
    User,
    UserPhoneNumber,
)
from down.apps.auth.serializers import UserSerializer
from down.apps.events.models import Event, Invitation
from down.apps.events.serializers import EventSerializer
from down.apps.friends.models import Friendship


class UserTests(APITestCase):

    def setUp(self):
        # Mock a user.
        self.user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                         username='tdog', image_url='http://imgur.com/tdog')
        self.user.save()

        # Mock the user's friend.
        self.friend = User(email='jclarke@gmail.com', name='Joan Clarke',
                           image_url='http://imgur.com/jcke')
        self.friend.save()
        friendship = Friendship(user1=self.user, user2=self.friend)
        friendship.save()

        # Mock an event that the user's invited to.
        self.event = Event(title='bars?!?!?!', creator=self.friend)
        self.event.save()
        self.invitation = Invitation(to_user=self.user, event=self.event)
        self.invitation.save()

    def test_get(self):
        url = reverse('user-detail', kwargs={'pk': self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the user.
        serializer = UserSerializer(self.user)
        json_user = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user)

    def test_put(self):
        url = reverse('user-detail', kwargs={'pk': self.user.id})
        new_name = 'Alan'
        data = {
            'email': self.user.email,
            'name': new_name,
            'username': self.user.username,
            'image_url': self.user.image_url,
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should update the user.
        user = User.objects.get(id=self.user.id)
        self.assertEqual(user.name, new_name)

        # It should return the user.
        serializer = UserSerializer(user)
        json_user = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user)

    def test_get_by_ids(self):
        url = reverse('user-list')
        ids = ','.join([unicode(self.user.id)])
        url += '?ids=' + ids
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the users.
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

    def test_friends(self):
        url = reverse('user-friends', kwargs={'pk': self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return a list of the user's friends.
        serializer = UserSerializer([self.friend], many=True)
        json_friends = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_friends)

    def test_invited_events(self):
        url = reverse('user-invited-events', kwargs={'pk': self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return a list of the user's invitations.
        serializer = EventSerializer([self.event], many=True)
        json_events = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_events)


class SocialAccountTests(APITestCase):
    
    def setUp(self):
        self.url = reverse('social-account-login')
        self.profile_url = 'https://graph.facebook.com/v2.2/me'
        self.user = User()
        self.user.save()
        self.token = Token(user=self.user)
        self.token.save()

        # Authorize the requests with the user's token.
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    @httpretty.activate
    def test_create(self):
        facebook_token = 'asdf123'
        facebook_user_id = 1207059
        email = 'aturing@gmail.com'
        name = 'Alan Tdog Turing'
        image_url = 'https://graph.facebook.com/v2.2/{id}/picture'.format(
                id=facebook_user_id)
        hometown = 'Paddington, London'
        friend_id = '10101293050283881'

        # Mock the user's friend.
        friend = User(email='jclarke@gmail.com', name='Joan Clarke')
        friend.save()
        friend_account = SocialAccount(user=friend,
                                       provider=SocialAccount.FACEBOOK,
                                       uid=friend_id)
        friend_account.save()

        # Request the user's profile.
        body = json.dumps({
            'id': facebook_user_id,
            'email': email,
            'name': name,
            'hometown': hometown,
        })
        httpretty.register_uri(httpretty.GET, self.profile_url, body=body,
                               content_type='application/json')

        # Request the user's friendlist.
        body = json.dumps({
            'data': [{
                'name': 'Joan Clarke', 
                'id': '10101293050283881',
            }],
        })
        friends_url = 'https://graph.facebook.com/v2.2/me/friends'
        httpretty.register_uri(httpretty.GET, friends_url, body=body,
                               content_type='application/json')

        data = {'access_token': facebook_token}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should update the user.
        user = User.objects.get(id=self.user.id, email=email, name=name,
                                image_url=image_url)

        # It should create the user's social account.
        profile = {
            'access_token': facebook_token,
            'id': facebook_user_id,
            'email': email,
            'name': name,
            'image_url': image_url,
            'hometown': hometown,
        }
        account = SocialAccount.objects.get(user=self.user,
                                            provider=SocialAccount.FACEBOOK,
                                            uid=facebook_user_id)
        self.assertEqual(account.profile, profile)

        # It should give Facebook the access token.
        params = {'access_token': [facebook_token]}
        self.assertEqual(httpretty.last_request().querystring, params)

        # It should create symmetrical facebook friendships.
        User.objects.get(id=self.user.id, facebook_friends__id=friend.id)
        User.objects.get(id=friend.id, facebook_friends__id=self.user.id)

        # It should return the user.
        self.user.email = email
        self.user.name = name
        self.user.image_url = image_url
        serializer = UserSerializer(self.user)
        json_user = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user)

    @httpretty.activate
    def test_create_bad_profile_request(self):
        facebook_token = 'asdf123'
        friend_id = '10101293050283881'

        # Mock the user's friend.
        friend = User(email='jclarke@gmail.com', name='Joan Clarke')
        friend.save()
        friend_account = SocialAccount(user=friend,
                                       provider=SocialAccount.FACEBOOK,
                                       uid=friend_id)
        friend_account.save()

        # Request the user's profile.
        httpretty.register_uri(httpretty.GET, self.profile_url, status=500,
                               content_type='application/json')

        data = {'access_token': facebook_token,
                'provider': SocialAccount.FACEBOOK,
                'user': self.user.id}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)


class AuthCodeTests(APITestCase):

    def setUp(self):
        self.url = reverse('authcode-list')
        self.phone_number = '+12345678910'

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

    def test_create_already_exists(self):
        mock_auth_code = AuthCode(phone=self.phone_number)
        mock_auth_code.save()

        response = self.client.post(self.url, {'phone': self.phone_number})

        # We shouldn't re-create an auth code which already exists 
        # for a given phone number
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SessionTests(APITestCase):
    
    @mock.patch('down.apps.auth.views.create_token')
    @mock.patch('down.apps.auth.views.uuid')
    def test_create(self, mock_uuid, mock_create_token):
        # Make sure no users have been created yet
        self.assertEquals(User.objects.count(), 0)

        # Generate a Firebase token.
        firebase_uuid = 9876
        firebase_token = 'qwer1234'
        mock_uuid.uuid1.return_value = firebase_uuid
        mock_create_token.return_value = firebase_token

        url = reverse('session')
        auth = AuthCode(phone='+12345678910')
        auth.save()
        response = self.client.post(url, {'phone': unicode(auth.phone), 'code': auth.code})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should delete the auth code
        with self.assertRaises(AuthCode.DoesNotExist):
            AuthCode.objects.get(code=auth.code, phone=auth.phone)

        # Make sure we've created a user for this number 
        user = User.objects.get()

        # Make sure the phone number was created
        UserPhoneNumber.objects.get(user=user, phone=auth.phone)

        # Get the token, which should've been created
        token = Token.objects.get(user=user)

        # It should generate a Firebase token.
        auth_payload = {'uid': unicode(firebase_uuid)}
        mock_create_token.assert_called_with(settings.FIREBASE_SECRET, auth_payload)

        # Check that the response is the user we're expecting
        user.authtoken = token.key
        user.firebase_token = firebase_token
        serializer = UserSerializer(user)
        json_user = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user)

    def test_create_bad_credentials(self):
        url = reverse('session')
        auth = AuthCode(phone='+12345678910')
        auth.save()
        response = self.client.post(url, {'phone': unicode(auth.phone), 'code': (auth.code + 'x')})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @mock.patch('down.apps.auth.views.create_token')
    @mock.patch('down.apps.auth.views.uuid')
    def test_user_already_created(self, mock_uuid, mock_create_token):
        firebase_uuid = 9876
        firebase_token = 'qwer1234'
        mock_uuid.uuid1.return_value = firebase_uuid
        mock_create_token.return_value = firebase_token

        # Mock an already created user
        mock_user = User()
        mock_user.save()

        phone_number = '+12345678910'
        mock_user_number = UserPhoneNumber(user=mock_user, phone=phone_number)
        mock_user_number.save()

        # User has already logged in, so mock their token
        token = Token(user=mock_user)
        token.save()

        url = reverse('session')
        auth = AuthCode(phone=phone_number)
        auth.save()

        response = self.client.post(url, {'phone': unicode(auth.phone), 'code': auth.code})
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
