from __future__ import unicode_literals
from django.core.urlresolvers import reverse
import mock
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APITestCase
from down.apps.auth.models import User
from down.apps.events.models import Event, Invitation
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

        # Mock two friendships.
        self.user_friendship = Friendship(user=self.user, friend=self.friend)
        self.user_friendship.save()
        self.friend_friendship = Friendship(user=self.friend, friend=self.user)
        self.friend_friendship.save()

        # Authorize the requests with the first user's token.
        self.token = Token(user=self.user)
        self.token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # Save URLs.
        self.list_url = reverse('friendship-list')
        self.detail_url = reverse('friendship-detail',
                                  kwargs={'pk': self.user_friendship.id})
        self.query_url = '{list_url}?user={user}&friend={friend}'.format(
                list_url=self.list_url,
                user=self.user.id,
                friend=self.friend.id)
        self.added_me_url = '{list_url}?friend={friend}'.format(
                list_url=self.list_url,
                friend=self.user.id)
        self.friend_url = reverse('friendship-friend')

    @mock.patch('down.apps.friends.serializers.send_message')
    def test_create(self, mock_send_message):
        # Delete the mocked friendships.
        self.user_friendship.delete()
        self.friend_friendship.delete()

        data = {
            'user': self.user.id,
            'friend': self.friend.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should save the friendship in the DB.
        friendship = Friendship.objects.get(user=self.user, friend=self.friend)

        # It should notify the friend that the user added them.
        user_ids = [self.friend.id]
        message = '{name} (@{username}) added you as a friend!'.format(
                name=self.user.name, username=self.user.username)
        mock_send_message.assert_any_call(user_ids, message, added_friend=True)

        # It should return the friendship.
        serializer = FriendshipSerializer(friendship)
        json_friendship = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_friendship)

    @mock.patch('down.apps.friends.serializers.send_message')
    def test_create_add_back(self, mock_send_message):
        # Delete the user's mocked friendship.
        self.user_friendship.delete()

        data = {
            'user': self.user.id,
            'friend': self.friend.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should save the friendship in the DB.
        friendship = Friendship.objects.get(user=self.user, friend=self.friend)

        # It should notify the friend that the user added them back (since they
        # already added the user as a friend).
        user_ids = [self.friend.id]
        message = '{name} (@{username}) added you back!'.format(
                name=self.user.name, username=self.user.username)
        mock_send_message.assert_any_call(user_ids, message)

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
        token = Token(user=self.friend)
        token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Try to create a friendship with a different user as user.
        data = {
            'user': self.user.id,
            'friend': self.friend.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_query_by_user_friend(self):
        response = self.client.get(self.query_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the friendship.
        serializer = FriendshipSerializer([self.user_friendship], many=True)
        json_friendships = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_friendships)

    def test_query_not_current_user(self):
        # Mock another user.
        user = User(email='guido@gmail.com', name='Guido Van Rossum',
                    username='guido', image_url='http://imgur.com/guido')
        user.save()

        # Authorize the requests with the new user's token.
        token = Token(user=user)
        token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(self.query_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_query_added_me(self):
        response = self.client.get(self.added_me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the friendship with the user as the friend.
        serializer = FriendshipSerializer([self.friend_friendship], many=True)
        json_friendships = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_friendships)

    def test_query_added_someone_else(self):
        url = '{list_url}?friend={friend}'.format(list_url=self.list_url,
                                                  friend=self.friend.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_query_other_user_added(self):
        url = '{list_url}?user={user}'.format(list_url=self.list_url,
                                              user=self.friend.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # It should delete the friendship.
        with self.assertRaises(Friendship.DoesNotExist):
            Friendship.objects.get(id=self.user_friendship.id)

    def test_delete_not_current_user(self):
        # Authorize the requests with the second user's token.
        token = Token(user=self.friend)
        token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_friend(self):
        data = {'friend': self.friend.id}
        response = self.client.delete(self.friend_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should delete the friendship.
        with self.assertRaises(Friendship.DoesNotExist):
            Friendship.objects.get(id=self.user_friendship.id)
