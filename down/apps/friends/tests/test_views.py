from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APITestCase
from down.apps.auth.models import User
from down.apps.friends.models import Friendship
from down.apps.friends.serializers import FriendshipSerializer


class FriendshipTests(APITestCase):

    def setUp(self):
        # Mock two users.
        self.user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                          username='tdog', image_url='http://imgur.com/tdog')
        self.user.save()
        self.friend = User(email='jclarke@gmail.com', name='Joan Clarke',
                          username='clarkie', image_url='http://imgur.com/jcke')
        self.friend.save()

        # Authorize the requests with the first user's token.
        self.token = Token(user=self.user)
        self.token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # Save URLs.
        self.list_url = reverse('friendship-list')
        self.query_url = '{list_url}?user={user}&friend={friend}'.format(
                list_url=self.list_url,
                user=self.user.id,
                friend=self.friend.id)

    def test_create(self):
        data = {
            'user': self.user.id,
            'friend': self.friend.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should save the friendship in the DB.
        friendship = Friendship.objects.get(user=self.user, friend=self.friend)

        # It should return the friendship.
        serializer = FriendshipSerializer(friendship)
        json_friendship = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_friendship)

    def test_create_not_logged_in(self):
        # Remove the user's credentials.
        self.client.credentials()

        response = self.client.post(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_not_current_user(self):
        # Authorize the requests with the second user's token.
        self.token = Token(user=self.friend)
        self.token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # Try to create a friendship with a different user as user.
        data = {
            'user': self.user.id,
            'friend': self.friend.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_query_by_user_friend(self):
        # Mock a friendship.
        friendship = Friendship(user=self.user, friend=self.friend)
        friendship.save()

        response = self.client.get(self.query_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the friendship.
        serializer = FriendshipSerializer([friendship], many=True)
        json_friendships = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_friendships)

    def test_query_not_current_user(self):
        # Authorize the requests with the second user's token.
        self.token = Token(user=self.friend)
        self.token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        response = self.client.get(self.query_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
