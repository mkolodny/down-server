from __future__ import unicode_literals
from django.core.urlresolvers import reverse
import mock
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APITestCase
from down.apps.auth.models import User
from down.apps.events.models import AllFriendsInvitation, Event, Invitation
from down.apps.friends.models import Friendship
from down.apps.friends.serializers import FriendshipSerializer


class FriendshipTests(APITestCase):

    # We have to mock the function that sends push notifications, since 
    # adding users as friends will send push notifications.
    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def setUp(self, mock_send):
        # Mock two users.
        self.user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                          username='tdog', image_url='http://imgur.com/tdog')
        self.user.save()
        self.friend = User(email='jclarke@gmail.com', name='Joan Clarke',
                          username='clarkie', image_url='http://imgur.com/jcke')
        self.friend.save()

        # Mock two friendships.
        self.friendship = Friendship(user=self.user, friend=self.friend)
        self.friendship.save()
        self.other_friendship = Friendship(user=self.friend, friend=self.user)
        self.other_friendship.save()

        # Authorize the requests with the first user's token.
        self.token = Token(user=self.user)
        self.token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # Save URLs.
        self.list_url = reverse('friendship-list')
        self.detail_url = reverse('friendship-detail',
                                  kwargs={'pk': self.friendship.id})
        self.query_url = '{list_url}?user={user}&friend={friend}'.format(
                list_url=self.list_url,
                user=self.user.id,
                friend=self.friend.id)
        self.added_me_url = '{list_url}?friend={friend}'.format(
                list_url=self.list_url,
                friend=self.user.id)
        self.friend_url = reverse('friendship-friend')

    # We have to mock the function that sends push notifications, since 
    # adding users as friends will send push notifications.
    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_create(self, mock_send):
        # Delete the mocked friendship.
        self.friendship.delete()

        # Create an new event with an open invitation.
        event = Event(creator=self.user, title='Ex Machina')
        event.save()
        all_friends_invitation = AllFriendsInvitation(from_user=self.user,
                                                      event=event)
        all_friends_invitation.save()

        # Save the most recent time the event was updated.
        updated_at = event.updated_at

        data = {
            'user': self.user.id,
            'friend': self.friend.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should save the friendship in the DB.
        friendship = Friendship.objects.get(user=self.user, friend=self.friend)

        # It should create an open invitation for the user.
        Invitation.objects.get(event=event, from_user=self.user,
                               to_user=self.friend, open=True)

        # It should update the event.
        event = Event.objects.get(id=event.id)
        self.assertGreater(event.updated_at, updated_at)

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
        serializer = FriendshipSerializer([self.friendship], many=True)
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
        serializer = FriendshipSerializer([self.other_friendship], many=True)
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
            Friendship.objects.get(id=self.friendship.id)

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
            Friendship.objects.get(id=self.friendship.id)

    """
    def test_acknowledge_added_me(self):
        data = {
            'id': self.friendship.id,
            'user': self.friendship.user_id,
            'friend': self.friendship.friend_id,
            'acknowledged': self.friendship.acknowledged,
        }
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should update the friendship.
        Friendship.objects.get(**data)

    def test_acknowledge_added_me_not_current_user(self):
        # Authorize the requests with the second user's token.
        token = Token(user=self.friend)
        token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.put(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    """
