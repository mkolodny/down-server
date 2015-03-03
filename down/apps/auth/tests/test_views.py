from __future__ import unicode_literals
import json
import mock
from urllib import urlencode
from django.conf import settings
from django.core.urlresolvers import reverse
import httpretty
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APITestCase
from down.apps.auth.models import SocialAccount, User
from down.apps.friends.models import Friendship
from down.apps.auth.serializers import UserSerializer


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

    def test_get(self):
        url = reverse('user-detail', kwargs={'pk': self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the user.
        serializer = UserSerializer(self.user)
        json_user = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user)

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


class SocialAccountTests(APITestCase):

    @mock.patch('down.apps.auth.views.create_token')
    @httpretty.activate
    def test_create(self, mock_create_token):
        facebook_token = 'asdf123'
        facebook_user_id = 1207059
        email = 'aturing@gmail.com'
        name = 'Alan Tdog Turing'
        image_url = 'https://graph.facebook.com/v2.2/{id}/picture'.format(
                id=facebook_user_id)
        hometown = 'Paddington, London'
        friend_id = '10101293050283881'
        firebase_token = 'qwer1234'

        # Mock the user's friend.
        friend = User(email='jclarke@gmail.com', name='Joan Clarke')
        friend.save()
        friend_account = SocialAccount(user=friend,
                                       provider=SocialAccount.FACEBOOK,
                                       uid=friend_id)
        friend_account.save()

        # Request the user's profile.
        body = json.dumps({
            'data': {
                'id': facebook_user_id,
                'email': email,
                'name': name,
                'hometown': hometown,
            },
        })
        url = 'https://graph.facebook.com/v2.2/me'
        httpretty.register_uri(httpretty.GET, url, body=body,
                               content_type='application/json')

        # Request the user's friendlist.
        body = json.dumps({
            'data': [{
              'name': 'Joan Clarke', 
              'id': '10101293050283881',
            }],
        })
        url = 'https://graph.facebook.com/v2.2/me/friends'
        httpretty.register_uri(httpretty.GET, url, body=body,
                               content_type='application/json')

        # Generate a Firebase token.
        mock_create_token.return_value = firebase_token

        url = reverse('social-account-login')
        data = {'access_token': 'asdf123'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create a user.
        user = User.objects.get(email=email, name=name, image_url=image_url)

        # It should create the user's social account.
        profile = {
            'access_token': facebook_token,
            'id': facebook_user_id,
            'email': email,
            'name': name,
            'image_url': image_url,
            'hometown': hometown,
        }
        account = SocialAccount.objects.get(user=user,
                                            provider=SocialAccount.FACEBOOK,
                                            uid=facebook_user_id)
        self.assertEqual(account.profile, profile)

        # It should give Facebook the access token.
        params = {'access_token': [facebook_token]}
        self.assertEqual(httpretty.last_request().querystring, params)

        # It should generate a Firebase token.
        auth_payload = {'uid': user.id}
        mock_create_token.assert_called_with(settings.FIREBASE_SECRET, auth_payload)

        # It should create friendships.
        Friendship.objects.get(user1=user, user2=friend)

        # It should log the user in.
        self.assertEqual(self.client.session['_auth_user_id'], user.id)

        # It should return the user.
        user.firebase_token = firebase_token
        serializer = UserSerializer(user)
        json_user = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_user)
