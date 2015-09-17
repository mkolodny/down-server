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

    def setUp(self):
        self.patcher = mock.patch('requests.patch')
        self.mock_patch = self.patcher.start()

        # Mock a user.
        self.user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                         username='tdog', image_url='http://imgur.com/tdog')
        self.user.save()
        self.user_phone = UserPhone(user=self.user, phone='+14388843460')
        self.user_phone.save()

        # Mock the user's friend.
        self.friend1 = User(email='jclarke@gmail.com', name='Joan Clarke',
                            username='jcke', image_url='http://imgur.com/jcke',
                            location='POINT(40.7027217 -73.9891945)')
        self.friend1.save()
        self.friendship = Friendship(user=self.user, friend=self.friend1)
        self.friendship.save()
        self.friendship = Friendship(user=self.friend1, friend=self.user)
        self.friendship.save()

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
        expected_message = ('{name} suggested: {activity} at {place} on {date}'
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
        expected_message = ('{name} suggested: {activity} at {place} on {date}'
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

        expected_message = ('{name} suggested: {activity} at {place}'
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
        expected_message = ('{name} suggested: {activity} on {date}'
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
        expected_message = ('{name} suggested: {activity} on {date}'
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

        expected_message = ('{name} suggested: {activity}'
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
