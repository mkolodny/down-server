from __future__ import unicode_literals
import mock
from push_notifications.models import APNSDevice
from rest_framework.test import APITestCase
from down.apps.auth.models import User
from down.apps.friends.models import Friendship

class FriendTests(APITestCase):

    def setUp(self):
        self.patcher = mock.patch('requests.patch')
        self.mock_patch = self.patcher.start()

        # Mock a user
        self.user = User(name='Alan Tdog Turing', username='tdog')
        self.user.save()

        # Mock the user's device.
        registration_id1 = ('2ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '10df230567037dcc4')
        device_id1 = 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F'
        self.user_apns_device = APNSDevice(registration_id=registration_id1,
                                      device_id=device_id1, name='iPhone, 8.2',
                                      user=self.user)
        self.user_apns_device.save()

        # Mock another user to be added as a friend by the user
        self.friend = User(name='Richard FoShizzle Feynman')
        self.friend.save()

        # Mock the friend's device.
        registration_id2 = ('3ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '20df230567037dcc4')
        device_id2 = 'E622E2F8-C36C-495A-93FC-0C247A3E6E5F'
        self.friend_apns_device = APNSDevice(registration_id=registration_id2,
                                      device_id=device_id2, name='iPhone, 8.2',
                                      user=self.friend)
        self.friend_apns_device.save()

    def tearDown(self):
        self.patcher.stop()

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_friendship_create_notify(self, mock_send): 
        # Add one direction of the friendship
        friendship = Friendship(user=self.user, friend=self.friend)
        friendship.save()

        # It should notify the friend that they were added by the user
        token = self.friend_apns_device.registration_id
        message = '{name} (@{username}) added you as a friend!'.format(
                name=self.user.name, username=self.user.username)

        mock_send.assert_any_call(registration_ids=[token], alert=message)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_friendship_create_notify_added_back(self, mock_send): 
        # Add one direction of the friendship
        friendship = Friendship(user=self.user, friend=self.friend)
        friendship.save()

        # Add the other direction of the friendship
        friendship = Friendship(user=self.friend, friend=self.user)
        friendship.save()

        # It should notify the user that they were added by the friend 
        # but with a different message!!!
        token = self.user_apns_device.registration_id
        message = '{name} added you back!'.format(name=self.friend.name)
        mock_send.assert_any_call(registration_ids=[token], alert=message)
