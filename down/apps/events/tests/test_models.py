from __future__ import unicode_literals
from datetime import datetime, timedelta
import json
import mock
import pytz
import random
import requests
import string
import time
from django.conf import settings
from django.utils import timezone
import httpretty
from push_notifications.models import APNSDevice
from rest_framework import status
from rest_framework.test import APITestCase
from down.apps.auth.models import User, UserPhone
from down.apps.events.models import (
    Event,
    Invitation,
    Place,
    get_invite_sms,
    get_local_dt,
)
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
        self.user_device = APNSDevice(registration_id=registration_id0,
                                       device_id=device_id0, name='iPhone, 8.2',
                                       user=self.user)
        self.user_device.save()

        # Mock the user's friend.
        self.friend1 = User(email='jclarke@gmail.com', name='Joan Clarke',
                            username='jcke', image_url='http://imgur.com/jcke',
                            location='POINT(40.7027217 -73.9891945)')
        self.friend1.save()
        self.friendship = Friendship(user=self.user, friend=self.friend1)
        self.friendship.save()
        self.friendship = Friendship(user=self.friend1, friend=self.user)
        self.friendship.save()
        registration_id1 = ('1ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '20df230567037dcc4')
        device_id1 = 'E622E2F8-C36C-495A-93FC-0C247A3E6E5F'
        self.friend1_device = APNSDevice(registration_id=registration_id1,
                                       device_id=device_id1, name='iPhone, 8.2',
                                       user=self.friend1)
        self.friend1_device.save()

        # Mock an event that the user's invited to.
        self.place = Place(name='Founder House',
                           geo='POINT(40.6898319 -73.9904645)')
        self.place.save()
        self.event = Event(title='bars?!?!?!', creator=self.friend1,
                           datetime=timezone.now(), place=self.place)
        self.event.save()

        # Save URLs.
        coords = self.place.geo.coords
        self.tz_url = ('http://api.geonames.org/timezone?lat={lat}'
                       '&lng={long}&username=mkolodny').format(lat=coords[0],
                                                               long=coords[1])

    def tearDown(self):
        self.patcher.stop()

    @mock.patch('down.apps.events.models.get_local_dt')
    def test_invite_sms_full(self, mock_get_local_dt):
        # Mock the timezone offset datetime.
        dt = datetime(2015, 5, 7, 10, 30, tzinfo=pytz.UTC)
        mock_get_local_dt.return_value = dt

        event_date = dt.strftime('%A, %b. %-d @ %-I:%M %p')
        expected_message = ('{name} invited you to {activity} at {place} on {date}'
                            '\n--\nSent from Down (http://down.life/app)').format(
                            name=self.friend1.name, activity=self.event.title,
                            place=self.place.name, date=event_date)
        message = get_invite_sms(self.friend1, self.event)
        self.assertEqual(message, expected_message)

        # It should call the mock the the right args.
        mock_get_local_dt.assert_called_with(self.event.datetime, self.place.geo)

    @mock.patch('down.apps.events.models.get_local_dt')
    def test_invite_sms_full_bad_offset_request(self, mock_get_local_dt):
        # Mock the bad response.
        mock_get_local_dt.return_value = None

        event_date = self.event.datetime.strftime('%A, %b. %-d')
        expected_message = ('{name} invited you to {activity} at {place} on {date}'
                            '\n--\nSent from Down (http://down.life/app)').format(
                            name=self.friend1.name, activity=self.event.title,
                            place=self.place.name, date=event_date)
        message = get_invite_sms(self.friend1, self.event)
        self.assertEqual(message, expected_message)

        # It should call the mock the the right args.
        mock_get_local_dt.assert_called_with(self.event.datetime, self.place.geo)

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

    @mock.patch('down.apps.events.models.get_local_dt')
    def test_invite_sms_no_place(self, mock_get_local_dt):
        # Remove the event's place.
        self.event.place = None
        self.event.save()

        # Mock the timezone aware datetime.
        dt = datetime(2015, 5, 7, 10, 30, tzinfo=pytz.UTC)
        mock_get_local_dt.return_value = dt

        event_date = dt.strftime('%A, %b. %-d @ %-I:%M %p')
        expected_message = ('{name} invited you to {activity} on {date}'
                            '\n--\nSent from Down (http://down.life/app)').format(
                            name=self.friend1.name, activity=self.event.title,
                            date=event_date)
        message = get_invite_sms(self.friend1, self.event)
        self.assertEqual(message, expected_message)

        # It should call the mock the the right args.
        mock_get_local_dt.assert_called_with(self.event.datetime,
                                              self.friend1.location)

    @mock.patch('down.apps.events.models.get_local_dt')
    def test_invite_sms_no_place_bad_offset_request(self, mock_get_local_dt):
        # Remove the event's place.
        self.event.place = None
        self.event.save()

        # Mock the bad response.
        mock_get_local_dt.return_value = None

        event_date = self.event.datetime.strftime('%A, %b. %-d')
        expected_message = ('{name} invited you to {activity} on {date}'
                            '\n--\nSent from Down (http://down.life/app)').format(
                            name=self.friend1.name, activity=self.event.title,
                            date=event_date)
        message = get_invite_sms(self.friend1, self.event)
        self.assertEqual(message, expected_message)

        # It should call the mock the the right args.
        mock_get_local_dt.assert_called_with(self.event.datetime,
                                              self.friend1.location)

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

    @httpretty.activate
    def test_get_local_dt(self):
        # Mock the Earth Tools response.
        body = '''
        <?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <geonames>
          <timezone tzversion="tzdata2015a">
            <countryCode>US</countryCode>
            <countryName>United States</countryName>
            <lat>33.6054149</lat>
            <lng>-112.125051</lng>
            <timezoneId>America/Phoenix</timezoneId>
            <dstOffset>-7.0</dstOffset>
            <gmtOffset>-7.0</gmtOffset>
            <rawOffset>-7.0</rawOffset>
            <time>2015-05-15 09:04</time>
            <sunrise>2015-05-15 05:27</sunrise>
            <sunset>2015-05-15 19:22</sunset>
          </timezone>
        </geonames>
        '''
        httpretty.register_uri(httpretty.GET, self.tz_url, body=body)

        dt = get_local_dt(self.event.datetime, self.place.geo)
        local_tz = pytz.timezone('America/Phoenix')
        datetime = self.event.datetime
        expected_dt = datetime.replace(tzinfo=pytz.utc).astimezone(local_tz)
        self.assertEqual(dt, expected_dt)

    @httpretty.activate
    def test_get_local_dt_bad_request(self):
        httpretty.register_uri(httpretty.GET, self.tz_url,
                               status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        dt = get_local_dt(self.event.datetime, self.place.geo)
        # It should return the original datetime.
        self.assertEqual(dt, None)

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
        self.friend2_device = APNSDevice(registration_id=registration_id2,
                                      device_id=device_id2, name='iPhone, 8.2',
                                      user=self.friend2)
        self.friend2_device.save()

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
        self.friend3_device = APNSDevice(registration_id=registration_id3,
                                         device_id=device_id3, name='iPhone, 8.2',
                                         user=self.friend3)
        self.friend3_device.save()

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
            self.friend1_device.registration_id, # friend1
            self.friend2_device.registration_id, # friend2
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

        # It should only notify the user who invited them.
        message = '{name} isn\'t down for {activity}'.format(
                name=self.user.name,
                activity=self.event.title)
        tokens = [
            self.user_device.registration_id,
        ]
        mock_send.assert_called_with(registration_ids=tokens, alert=message)
        self.assertEqual(mock_send.call_count, 1)
