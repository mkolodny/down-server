from __future__ import unicode_literals
import json
from django.core.urlresolvers import reverse
from django.test import TestCase
import httpretty
from rest_framework import status
from down.apps.auth.exceptions import ServiceUnavailable
from down.apps.auth.models import SocialAccount, User
from down.apps.auth.utils import get_facebook_friends
from down.apps.friends.models import Friendship


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

        # Mock the user having more than 25 friends on Down.
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
            }
        })
        httpretty.register_uri(httpretty.GET, next_url, body=body,
                               content_type='application/json')

        friends = get_facebook_friends(self.user)
        
        # It should return a queryset of the users facebook friends.
        self.assertEqual(list(friends), [friend1, friend2])

    @httpretty.activate
    def test_facebook_friends_bad_response(self):
        # Mock a bad response from Facebook when requesting the user's facebook
        # friends.
        httpretty.register_uri(httpretty.GET, self.friends_url,
                               status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        with self.assertRaises(ServiceUnavailable):
            get_facebook_friends(self.user)

    @httpretty.activate
    def test_facebook_friends_no_content(self):
        # Mock bad response data from Facebook when requesting the user's facebook
        # friends.
        httpretty.register_uri(httpretty.GET, self.friends_url, body='',
                               status=status.HTTP_200_OK)
        
        with self.assertRaises(ServiceUnavailable):
            get_facebook_friends(self.user)

    @httpretty.activate
    def test_facebook_friends_no_data(self):
        # Mock Facebook response data without a `data` property.
        httpretty.register_uri(httpretty.GET, self.friends_url, body=json.dumps({}),
                               status=status.HTTP_200_OK)
        
        with self.assertRaises(ServiceUnavailable):
            get_facebook_friends(self.user)
