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

        # Mock another friend.
        self.friend1 = User(email='mjordan@gmail.com', name='Michael Jordan',
                      image_url='http://imgur.com/mj')
        self.friend1.save()
        self.friendship = Friendship(user1=self.friend, user2=self.friend1)
        self.friendship.save()
        self.friendship = Friendship(user1=self.friend1, user2=self.friend)
        self.friendship.save()

        # Mock an event that the user's invited to.
        self.event = Event(title='bars?!?!?!', creator=self.friend)
        self.event.save()

        # Mock the invited user's device.
        registration_id1 = ('2ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '10df230567037dcc4')
        device_id1 = 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F'
        self.apns_device1 = APNSDevice(registration_id=registration_id1,
                                      device_id=device_id1, name='iPhone, 8.2',
                                      user=self.user)
        self.apns_device1.save()

        registration_id2 = ('3ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '20df230567037dcc4')
        device_id2 = 'E622E2F8-C36C-495A-93FC-0C247A3E6E5F'
        self.apns_device2 = APNSDevice(registration_id=registration_id2,
                                      device_id=device_id2, name='iPhone, 8.2',
                                      user=self.friend)
        self.apns_device2.save()

        registration_id3 = ('4ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '20df230567037dcc4')
        device_id3 = 'E622E2F8-C36C-495A-93FC-0C247A3E6E5F'
        self.apns_device3 = APNSDevice(registration_id=registration_id3,
                                      device_id=device_id3, name='iPhone, 8.2',
                                      user=self.friend1)
        self.apns_device3.save()

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_post_create_notify(self, mock_send):
        # Invite the user.
        invitation = Invitation(to_user=self.user, event=self.event)
        invitation.save()

        token = self.apns_device1.registration_id
        message = '{name} is down for {activity}'.format(
                name=self.event.creator.name,
                activity=self.event.title)
        mock_send.assert_called_once_with(registration_ids=[token], alert=message)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_post_invitation_accept_notify(self, mock_send):
        # Say that friend1 is down for the event.
        invitation = Invitation(to_user=self.friend1, event=self.event,
                                accepted=True)
        invitation.save()

        # Invite the user.
        invitation = Invitation(to_user=self.user, event=self.event)
        invitation.save()

        # The user accepts the invtation.
        invitation.accepted = True
        invitation.save()

        # It should notify the invited users.
        message = '{name} is also down for {activity}'.format(
                name=self.user.name,
                activity=self.event.title)
        tokens = [
            self.apns_device2.registration_id,
            self.apns_device3.registration_id,
        ]
        mock_send.assert_called_with(registration_ids=tokens, alert=message)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_post_invitation_accept_notify_creator_accepted(self, mock_send):
        # Say that friend1 is also down for the event.
        invitation = Invitation(to_user=self.friend1, event=self.event,
                                accepted=True)
        invitation.save()

        # Invite the user.
        invitation = Invitation(to_user=self.user, event=self.event)
        invitation.save()

        # The user accepts the invtation.
        invitation.accepted = True
        invitation.save()

        # It should notify the users who are already down for the event, as well
        # as the creator.
        message = '{name} is also down for {activity}'.format(
                name=self.user.name,
                activity=self.event.title)
        tokens = [
            self.apns_device2.registration_id,
            self.apns_device3.registration_id,
        ]
        mock_send.assert_called_with(registration_ids=tokens, alert=message)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_post_invitation_accept_already_accepted(self, mock_send):
        # Invite the user.
        invitation = Invitation(to_user=self.user, event=self.event)
        invitation.save()

        # The user accepts the invitation.
        invitation.accepted = True
        invitation.save()

        # Clear the mock's apns call count.
        mock_send.reset_mock()

        # The user still accepts the invitation, or has toggled the accept state.
        invitation.accepted = True
        invitation.save()

        # It should NOT (ugh..) send another notification.
        self.assertFalse(mock_send.called)
