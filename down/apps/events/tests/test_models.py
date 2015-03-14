from __future__ import unicode_literals
import mock
from push_notifications.models import APNSDevice
from rest_framework.test import APITestCase
from down.apps.auth.models import User
from down.apps.events.models import Event, Invitation
from down.apps.friends.models import Friendship


class InvitationTests(APITestCase):

    def setUp(self):
        # Mock a user.
        self.user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                         username='tdog', image_url='http://imgur.com/tdog')
        self.user.save()

        # Mock the user's friend.
        self.friend = User(email='jclarke@gmail.com', name='Joan Clarke',
                      image_url='http://imgur.com/jcke')
        self.friend.save()
        self.friendship = Friendship(user1=self.user, user2=self.friend)
        self.friendship.save()
        self.friendship = Friendship(user1=self.friend, user2=self.user)
        self.friendship.save()

        # Mock an event that the user's invited to.
        self.event = Event(title='bars?!?!?!', creator=self.friend)
        self.event.save()

        # Mock the invited user's device.
        registration_id = ('2ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '10df230567037dcc4')
        device_id = 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F'
        self.apns_device = APNSDevice(registration_id=registration_id,
                                      device_id=device_id, name='iPhone, 8.2',
                                      user=self.user)
        self.apns_device.save()

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_post_save_notify(self, mock_send):
        invitation = Invitation(to_user=self.user, event=self.event)
        invitation.save()

        token = self.apns_device.registration_id
        message = '{name} is down for {activity}'.format(
                name=self.event.creator.name,
                activity=self.event.title)
        mock_send.assert_called_once_with(registration_ids=[token], alert=message)
