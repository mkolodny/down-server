from __future__ import unicode_literals
import json
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
import httpretty
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ParseError
from rallytap.apps.auth.models import SocialAccount, User
from rallytap.apps.auth import utils
from rallytap.apps.friends.models import Friendship
from rallytap.apps.utils.exceptions import ServiceUnavailable


class FacebookFriendsTests(TestCase):

    def setUp(self):
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

        # Save URLs.
        self.friends_url = 'https://graph.facebook.com/v2.2/me/friends'

    @httpretty.activate
    def test_facebook_friends(self):
        # Mock two of the user's friends.
        friend1 = User(email='jclarke@gmail.com', name='Joan Clarke',
                       image_url='http://imgur.com/jcke',
                       location='POINT(40.7545645 -73.9813595)')
        friend1.save()
        friendship = Friendship(user=self.user, friend=friend1)
        friendship.save()
        friend1_social = SocialAccount(user=friend1,
                                       provider=SocialAccount.FACEBOOK,
                                       uid='20101293050283881',
                                       profile={'access_token': '2234asdf'})
        friend1_social.save()
        friend2 = User(email='htubman@gmail.com', name='Harriet Tubman',
                       image_url='http://imgur.com/tubby')
        friend2.save()
        friendship = Friendship(user=self.user, friend=friend2)
        friendship.save()
        friend2_social = SocialAccount(user=friend2,
                                       provider=SocialAccount.FACEBOOK,
                                       uid='30101293050283881',
                                       profile={'access_token': '3234asdf'})
        friend2_social.save()

        # Mock the user having more than 25 friends on rallytap.
        next_url = 'https://graph.facebook.com/v2.2/123/friends'
        body = json.dumps({
            'data': [{
                'name': 'Joan Clarke', 
                'id': friend1_social.uid,
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
                'id': friend2_social.uid,
            }],
            'paging': {
            },
        })
        httpretty.register_uri(httpretty.GET, next_url, body=body,
                               content_type='application/json')

        friends = utils.get_facebook_friends(self.user_social)
        
        # It should return a queryset of the users facebook friends.
        self.assertEqual(list(friends), [friend1, friend2])

    @httpretty.activate
    def test_facebook_friends_error(self):
        # Mock a bad response from Facebook when requesting the user's facebook
        # friends.
        httpretty.register_uri(httpretty.GET, self.friends_url,
                               status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        with self.assertRaises(ServiceUnavailable):
            utils.get_facebook_friends(self.user_social)

    @httpretty.activate
    def test_facebook_friends_expired_token(self):
        # Mock Facebook telling us that the user's access token has expired.
        httpretty.register_uri(httpretty.GET, self.friends_url,
                               status=status.HTTP_400_BAD_REQUEST)
        
        with self.assertRaises(ParseError):
            utils.get_facebook_friends(self.user_social)

    @httpretty.activate
    def test_facebook_friends_no_content(self):
        # Mock bad response data from Facebook when requesting the user's facebook
        # friends.
        httpretty.register_uri(httpretty.GET, self.friends_url, body='',
                               status=status.HTTP_200_OK)
        
        with self.assertRaises(ServiceUnavailable):
            utils.get_facebook_friends(self.user_social)

    @httpretty.activate
    def test_facebook_friends_no_friends(self):
        # Mock Facebook response data with no friends.
        body = json.dumps({'data': []})
        httpretty.register_uri(httpretty.GET, self.friends_url, body=body,
                               status=status.HTTP_200_OK)
        
        friends = utils.get_facebook_friends(self.user_social)
        self.assertEqual(list(friends), [])

    @httpretty.activate
    def test_facebook_friends_no_data(self):
        # Mock Facebook response data without a `data` property.
        httpretty.register_uri(httpretty.GET, self.friends_url, body=json.dumps({}),
                               status=status.HTTP_200_OK)
        
        with self.assertRaises(ServiceUnavailable):
            utils.get_facebook_friends(self.user_social)


class FacebookProfileTests(TestCase):

    def setUp(self):
        # Mock a user.
        self.user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                         first_name='Alan', last_name='Turing', username='tdog',
                         image_url='http://imgur.com/tdog',
                         location='POINT(50.7545645 -73.9813595)')
        self.user.save()
        """
        self.user_social = SocialAccount(user=self.user,
                                         provider=SocialAccount.FACEBOOK,
                                         uid='10101293050283881',
                                         profile={'access_token': '1234asdf'})
        self.user_social.save()
        """

        # Save Facebook data.
        self.fb_profile = {
            'id': 10101293050283881,
            'email': self.user.email,
            'name': self.user.name,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'hometown': 'New York, NY',
        }
        self.access_token = 'asdf123'

        # Save URLs.
        self.profile_url = 'https://graph.facebook.com/v2.2/me'

    @httpretty.activate
    def test_get(self):
        # Mock requesting the user's profile.
        body = json.dumps(self.fb_profile)
        httpretty.register_uri(httpretty.GET, self.profile_url, body=body,
                               content_type='application/json')

        profile = utils.get_facebook_profile(self.access_token)

        # It should make the request to Facebook with the access token.
        params = {'access_token': [self.access_token]}
        self.assertEqual(httpretty.last_request().querystring, params)

        # It should return the user's facebook profile.
        expected_profile = self.fb_profile
        expected_profile['image_url'] = ('https://graph.facebook.com/v2.2/{id}/'
                                         'picture').format(id=self.fb_profile['id'])
        expected_profile['access_token'] = self.access_token
        self.assertEqual(profile, expected_profile)

    @httpretty.activate
    def test_get_bad_status(self):
        # Mock a bad response from Facebook when requesting the user's facebook
        # profile.
        httpretty.register_uri(httpretty.GET, self.profile_url,
                               status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        with self.assertRaises(ServiceUnavailable):
            utils.get_facebook_profile(self.access_token)


class MeteorLoginTests(TestCase):

    def setUp(self):
        self.user = User()
        self.user.save()
        self.token = Token(user=self.user)
        self.token.save()

        # Save URLs.
        self.meteor_url = '{meteor_url}/users'.format(
                meteor_url=settings.METEOR_URL)

    @httpretty.activate
    def test_meteor_login(self):
        # Mock a successful meteor server response.
        httpretty.register_uri(httpretty.POST, self.meteor_url,
                               content_type='application/json')

        utils.meteor_login(self.user.id, self.token)

        # It should authenticate the user on the meteor server.
        self.assertEqual(httpretty.last_request().body, json.dumps({
            'user_id': self.user.id,
            'password': self.token.key,
        }))
        auth_header = 'Token {api_key}'.format(api_key=settings.METEOR_KEY)
        self.assertEqual(httpretty.last_request().headers['Authorization'],
                         auth_header)
        self.assertEqual(httpretty.last_request().headers['Content-Type'],
                         'application/json')

    @httpretty.activate
    def test_meteor_login_bad_status(self):
        # Mock an unsuccessful meteor server response.
        httpretty.register_uri(httpretty.POST, self.meteor_url,
                               content_type='application/json',
                               status=status.HTTP_503_SERVICE_UNAVAILABLE)

        with self.assertRaises(ServiceUnavailable):
            utils.meteor_login(self.user.id, self.token)
