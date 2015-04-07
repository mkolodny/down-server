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
from down.apps.auth.serializers import UserSerializer, UserPhoneNumberSerializer
from down.apps.events.models import Event, Invitation
from down.apps.events.serializers import EventSerializer
from down.apps.friends.models import Friendship


class UserTests(APITestCase):

    def setUp(self):
        self.patcher = mock.patch('requests.patch')
        self.mock_patch = self.patcher.start()

        # Mock a user.
        self.user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                         username='tdog', image_url='http://imgur.com/tdog')
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

        # Mock the user's friend.
        self.friend = User(email='jclarke@gmail.com', name='Joan Clarke',
                           image_url='http://imgur.com/jcke')
        self.friend.save()
        friendship = Friendship(user=self.user, friend=self.friend)
        friendship.save()
        self.friend_social = SocialAccount(user=self.friend,
                                           provider=SocialAccount.FACEBOOK,
                                           uid='20101293050283881',
                                           profile={'access_token': '2234asdf'})
        self.friend_social.save()

        # Mock an event that the user's invited to.
        self.event = Event(title='bars?!?!?!', creator=self.friend)
        self.event.save()
        self.invitation = Invitation(to_user=self.user, event=self.event)
        self.invitation.save()

        # Mock the users' phone numbers.
        self.friend_phone = UserPhoneNumber(user=self.friend, phone='+12036227310')
        self.friend_phone.save()
        self.user_phone = UserPhoneNumber(user=self.user, phone='+14388843460')
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
        detail_url = reverse('user-detail', kwargs={'pk': self.friend.id})
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

    @httpretty.activate
    def test_facebook_friends(self):
        # Mock the user's facebook friends.
        body = json.dumps({
            'data': [{
                'name': 'Joan Clarke', 
                'id': self.friend_social.uid,
            }],
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
        serializer = UserSerializer([self.friend], many=True)
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
        self.url = reverse('social-account-login')
        self.profile_url = 'https://graph.facebook.com/v2.2/me'

        # Mock the user.
        self.user = User()
        self.user.save()
        self.phone = UserPhoneNumber(user=self.user, phone='+12036227310')
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

    @httpretty.activate
    def test_create(self):
        facebook_token = 'asdf123'
        facebook_user_id = 1207059
        email = 'aturing@gmail.com'
        name = 'Alan Tdog Turing'
        image_url = 'https://graph.facebook.com/v2.2/{id}/picture'.format(
                id=facebook_user_id)
        hometown = 'Paddington, London'

        # Request the user's profile.
        body = json.dumps({
            'id': facebook_user_id,
            'email': email,
            'name': name,
            'hometown': hometown,
        })
        httpretty.register_uri(httpretty.GET, self.profile_url, body=body,
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

        # It should return the user.
        self.user.email = email
        self.user.name = name
        self.user.image_url = image_url
        serializer = UserSerializer(self.user)
        json_user = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user)

    @httpretty.activate
    def test_create_bad_profile_request(self):
        # Request the user's profile.
        httpretty.register_uri(httpretty.GET, self.profile_url, status=500,
                               content_type='application/json')

        data = {
            'access_token': 'asdf123',
            'provider': SocialAccount.FACEBOOK,
            'user': self.user.id,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @httpretty.activate
    def test_create_already_exists(self):
        # Users who've already signed up will have an email, username and
        # image_url. So mock a user that already has those attributes.
        facebook_user_id = 1207059
        image_url = 'https://graph.facebook.com/v2.2/{id}/picture'.format(
                id=facebook_user_id)
        user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                    image_url=image_url)
        user.save()

        # Request the user's profile.
        body = json.dumps({
            'id': facebook_user_id,
            'email': user.email,
            'name': user.name,
            'image_url': user.image_url,
        })
        httpretty.register_uri(httpretty.GET, self.profile_url, body=body,
                               content_type='application/json')

        data = {'access_token': 'asdf123'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should delete the old user.
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(id=self.user.id)

        # It should update the user's token to point to the old user.
        Token.objects.get(key=self.token.key, user=user)

        # It should point the old user's phone number to the new user.
        UserPhoneNumber.objects.get(id=self.phone.id, user=user)

    def test_create_not_logged_in(self):
        # Log the user out.
        self.client.credentials()

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


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

    @mock.patch('down.apps.auth.views.TwilioRestClient')
    def test_create_already_exists(self, mock_TwilioRestClient):
        # Mock the Twilio SMS API.
        mock_client = mock.MagicMock()
        mock_TwilioRestClient.return_value = mock_client

        auth = AuthCode(phone=self.phone_number)
        auth.save()

        response = self.client.post(self.url, {'phone': self.phone_number})

        # We shouldn't re-create an auth code which already exists 
        # for a given phone number
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should init the Twilio client with the proper params.
        mock_TwilioRestClient.assert_called_with(settings.TWILIO_ACCOUNT,
                                                 settings.TWILIO_TOKEN)

        # It should text the user the auth code.
        message = 'Your Down code: {}'.format(auth.code)
        mock_client.messages.create.assert_called_with(to=self.phone_number, 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=message)


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
        UserPhoneNumber.objects.get(user=user, phone=auth.phone)

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

        data = {'phone': unicode(auth.phone), 'code': auth.code}
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


class UserPhoneNumberViewSet(APITestCase):

    def setUp(self):
        # Mock two users.
        self.user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                         username='tdog', image_url='http://imgur.com/tdog')
        self.user.save()
        self.friend = User(email='jclarke@gmail.com', name='Joan Clarke',
                           image_url='http://imgur.com/jcke')
        self.friend.save()

        # Mock the users' phone numbers.
        self.friend_phone = UserPhoneNumber(user=self.friend, phone='+12036227310')
        self.friend_phone.save()
        self.user_phone = UserPhoneNumber(user=self.user, phone='+14388843460')
        self.user_phone.save()

        # Save URLs.
        self.list_url = reverse('userphone')

    def test_query_by_phones(self):
        data = {'phones': [unicode(self.user_phone.phone)]}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return a list with the user.
        serializer = UserPhoneNumberSerializer([self.user_phone], many=True)
        json_user_phones = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user_phones)


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
