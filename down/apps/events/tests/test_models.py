from __future__ import unicode_literals
from django.conf import settings
from django.utils import timezone
import json
import mock
import random
import requests
import string
from push_notifications.models import APNSDevice
from rest_framework.test import APITestCase
from down.apps.auth.models import User, UserPhone
from down.apps.events.models import Event, Invitation, Place, get_invite_sms
from down.apps.friends.models import Friendship


class InvitationTests(APITestCase):

    # We have to mock the function that sends push notifications, since adding
    # mock friends will send push notifications.
    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def setUp(self, mock_send):
        self.patcher = mock.patch('requests.patch')
        self.mock_patch = self.patcher.start()

        # Mock a user.
        self.user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                         username='tdog', image_url='http://imgur.com/tdog')
        self.user.save()
        self.user_phone = UserPhone(user=self.user, phone='+14388843460')
        self.user_phone.save()
        registration_id0 = ('0ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                            '10df230567037dcc4')
        device_id0 = 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F'
        self.apns_device0 = APNSDevice(registration_id=registration_id0,
                                       device_id=device_id0, name='iPhone, 8.2',
                                       user=self.user)
        self.apns_device0.save()

        # Mock the user's friend.
        self.friend1 = User(email='jclarke@gmail.com', name='Joan Clarke',
                            username='jcke', image_url='http://imgur.com/jcke')
        self.friend1.save()
        self.friendship = Friendship(user=self.user, friend=self.friend1)
        self.friendship.save()
        self.friendship = Friendship(user=self.friend1, friend=self.user)
        self.friendship.save()
        registration_id1 = ('1ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '20df230567037dcc4')
        device_id1 = 'E622E2F8-C36C-495A-93FC-0C247A3E6E5F'
        self.apns_device1 = APNSDevice(registration_id=registration_id1,
                                       device_id=device_id1, name='iPhone, 8.2',
                                       user=self.friend1)
        self.apns_device1.save()

        # Mock an event that the user's invited to.
        self.place = Place(name='Founder House',
                           geo='POINT(40.6898319 -73.9904645)')
        self.place.save()
        self.event = Event(title='bars?!?!?!', creator=self.friend1,
                           datetime=timezone.now(), place=self.place)
        self.event.save()



    def tearDown(self):
        self.patcher.stop()

    def test_invite_sms_full(self):
        event_date = self.event.datetime.strftime('%A, %b. %-d @ %-I:%M %p')
        expected_message = ('{name} invited you to {activity} at {place} on {date}'
                            '\n--\nSent from Down (http://down.life/app)').format(
                            name=self.friend1.name, activity=self.event.title,
                            place=self.place.name, date=event_date)
        message = get_invite_sms(self.friend1, self.event)
        self.assertEqual(message, expected_message)

    def test_invite_sms_no_date(self):
        # Remove the event's date.
        self.event.datetime = None
        self.event.save()

        expected_message = ('{name} invited you to {activity} at {place}'
                            '\n--\nSent from Down (http://down.life/app)').format(
                            name=self.friend1.name, activity=self.event.title,
                            place=self.place.name)
        message = get_invite_sms(self.friend1, self.event)
        self.assertEqual(message, expected_message)

    def test_invite_sms_no_place(self):
        # Remove the event's place.
        self.event.place = None
        self.event.save()

        event_date = self.event.datetime.strftime('%A, %b. %-d @ %-I:%M %p')
        expected_message = ('{name} invited you to {activity} on {date}'
                            '\n--\nSent from Down (http://down.life/app)').format(
                            name=self.friend1.name, activity=self.event.title,
                            date=event_date)
        message = get_invite_sms(self.friend1, self.event)
        self.assertEqual(message, expected_message)

    def test_invite_sms_no_place_or_date(self):
        # Remove the event's place and date.
        self.event.place = None
        self.event.datetime = None
        self.event.save()

        expected_message = ('{name} invited you to {activity}'
                            '\n--\nSent from Down (http://down.life/app)').format(
                            name=self.friend1.name, activity=self.event.title)
        message = get_invite_sms(self.friend1, self.event)
        self.assertEqual(message, expected_message)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def mock_friend2(self, mock_send):
        """
        Mock another friend.
        """
        self.friend2 = User(email='mjordan@gmail.com', name='Michael Jordan',
                            username='mj', image_url='http://imgur.com/mj')
        self.friend2.save()
        self.friendship = Friendship(user=self.user, friend=self.friend2)
        self.friendship.save()
        self.friendship = Friendship(user=self.friend2, friend=self.user)
        self.friendship.save()
        registration_id2 = ('2ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '20df230567037dcc4')
        device_id2 = 'E622E2F8-C36C-495A-93FC-0C247A3E6E5F'
        self.apns_device2 = APNSDevice(registration_id=registration_id2,
                                      device_id=device_id2, name='iPhone, 8.2',
                                      user=self.friend2)
        self.apns_device2.save()

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_post_invitation_accept_notify(self, mock_send):
        # Mock another friend.
        self.mock_friend2()

        # Mock one more friend.
        self.friend3 = User(email='mcurie@gmail.com', name='Marie Curie',
                            username='mcurie', image_url='http://imgur.com/mcurie')
        self.friend3.save()
        self.friendship = Friendship(user=self.user, friend=self.friend3)
        self.friendship.save()
        self.friendship = Friendship(user=self.friend3, friend=self.user)
        self.friendship.save()
        registration_id3 = ('3ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                            '20df230567037dcc4')
        device_id3 = 'E622E2F8-C36C-495A-93FC-0C247A3E6E5F'
        self.apns_device3 = APNSDevice(registration_id=registration_id3,
                                      device_id=device_id3, name='iPhone, 8.2',
                                      user=self.friend3)
        self.apns_device3.save()

        # Invite the creator to the event they created
        self.invitation = Invitation(from_user=self.friend1, to_user=self.friend1,
                                event=self.event, response=Invitation.ACCEPTED)
        self.invitation.save()

        # Say that friend2 hasn't responded yet.
        invitation = Invitation(from_user=self.friend1, to_user=self.friend2,
                                event=self.event, response=Invitation.NO_RESPONSE)
        invitation.save()

        # Say that friend3 is not down for the event.
        invitation = Invitation(from_user=self.friend1, to_user=self.friend3,
                                event=self.event, response=Invitation.DECLINED)
        invitation.save()

        # Invite the user.
        invitation = Invitation(from_user=self.friend1, to_user=self.user,
                                event=self.event)
        invitation.save()

        # Clear the mock's call count
        mock_send.reset_mock()

        # The user accepts the invtation.
        invitation.response = Invitation.ACCEPTED
        invitation.save()

        # It should notify the invited users who are either down, or haven't
        # responded yet.
        message = '{name} is also down for {activity}'.format(
                name=self.user.name,
                activity=self.event.title)
        tokens = [
            self.apns_device1.registration_id, # friend1
            self.apns_device2.registration_id, # friend2
        ]
        mock_send.assert_called_with(registration_ids=tokens, alert=message)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_post_invitation_creator_accept_no_notify(self, mock_send):
        # Mock another friend.
        self.mock_friend2()

        # Say that friend2 hasn't responded yet.
        invitation = Invitation(from_user=self.friend1, to_user=self.friend2,
                                event=self.event, response=Invitation.NO_RESPONSE)
        invitation.save()

        # Clear the mock's call count
        mock_send.reset_mock()

        # Invite the user, accepted by default.
        invitation = Invitation(from_user=self.friend1, to_user=self.friend1,
                                event=self.event, response=Invitation.ACCEPTED)
        invitation.save()

        # we should not notify anyone that the creator of the event
        # is down (as this happens by default)
        self.assertEqual(mock_send.call_count, 0)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_post_invitation_decline(self, mock_send):
        # Mock another friend.
        self.mock_friend2()

        # Invite the friend.
        invitation = Invitation(from_user=self.user, to_user=self.friend2,
                                event=self.event)
        invitation.save()

        # Invite the user.
        invitation = Invitation(from_user=self.user, to_user=self.user,
                                event=self.event)
        invitation.save()

        # Clear the mock's apns call count.
        mock_send.reset_mock()

        # The user declines the invitation.
        invitation.response = Invitation.DECLINED
        invitation.save()

        # It should only notify the event creator.
        message = '{name} isn\'t down for {activity}'.format(
                name=self.user.name,
                activity=self.event.title)
        tokens = [
            self.apns_device2.registration_id, # friend1
        ]
        mock_send.assert_called_with(registration_ids=tokens, alert=message)
