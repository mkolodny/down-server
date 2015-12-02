from __future__ import unicode_literals
from django.core.urlresolvers import reverse
import mock
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APITestCase
from rallytap.apps.auth.models import User
from rallytap.apps.events.models import Event
from rallytap.apps.friends.models import Friendship
from rallytap.apps.friends.serializers import FriendshipSerializer


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
        self.delete_url = reverse('friendship-friend')
        self.send_message_url = reverse('friendship-messages', kwargs={
            'pk': self.friend.id,
        })

    @mock.patch('rallytap.apps.friends.serializers.send_message')
    @mock.patch('rallytap.apps.friends.serializers.add_members')
    def test_create(self, mock_add_members, mock_send_message):
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

        # It should create a chat in the meteor database.
        chat_id = '{user_id},{friend_id}'.format(user_id=self.user.id,
                                                 friend_id=self.friend.id)
        mock_add_members.assert_any_call(chat_id, [self.user.id, self.friend.id])

        # It should return the friendship.
        serializer = FriendshipSerializer(friendship)
        json_friendship = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_friendship)

    @mock.patch('rallytap.apps.friends.serializers.send_message')
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

    def test_delete_friend(self):
        data = {'friend': self.friend.id}
        response = self.client.delete(self.delete_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should delete the friendship.
        with self.assertRaises(Friendship.DoesNotExist):
            Friendship.objects.get(id=self.user_friendship.id)

    @mock.patch('rallytap.apps.friends.views.send_message')
    def test_send_message(self, mock_send_message):
        data = {'text': 'So down!'}
        response = self.client.post(self.send_message_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should send the friend a message.
        user_ids = [self.friend.id]
        message = '{name}: {text}'.format(name=self.user.name, text=data['text'])
        mock_send_message.assert_any_call(user_ids, message)
