from __future__ import unicode_literals
from datetime import timedelta
import json
from django.conf import settings
from django.test import TestCase
from django.utils import timezone
import httpretty
import requests
from rest_framework import status
from rallytap.apps.auth.models import User
from rallytap.apps.events.models import Event
from ..utils import add_members


class MeteorTests(TestCase):

    def setUp(self):
        # Save re-used data.
        self.user = User(name='Barack Obama', first_name='Barack',
                         last_name='Obama', image_url='http:/facebook.com/img/prez')
        self.user.save()
        self.event = Event(title='breaking it down', creator=self.user)
        self.event.save()

        # Save URLs.
        self.add_members_url = '{meteor_url}/events/{event_id}/members'.format(
                meteor_url=settings.METEOR_URL, event_id=self.event.id)

    @httpretty.activate
    def test_add_members_event_no_date(self):
        # Mock the response from the meteor server.
        httpretty.register_uri(httpretty.POST, self.add_members_url)

        add_members(self.event, self.user.id)

        twenty_four_hrs_later = self.event.created_at + timedelta(hours=24)
        self.assertEqual(httpretty.last_request().body, json.dumps({
            'user_id': self.user.id,
            'expires_at': twenty_four_hrs_later.isoformat(),
        }))
        auth_header = 'Token {api_key}'.format(api_key=settings.METEOR_KEY)
        self.assertEqual(httpretty.last_request().headers['Authorization'],
                         auth_header)
        self.assertEqual(httpretty.last_request().headers['Content-Type'],
                         'application/json')

    @httpretty.activate
    def test_add_members_event_has_date(self):
        # Give the event a date.
        self.event.datetime = timezone.now()

        # Mock the response from the meteor server.
        httpretty.register_uri(httpretty.POST, self.add_members_url)

        add_members(self.event, self.user.id)

        twenty_four_hrs_later = self.event.datetime + timedelta(hours=24)
        self.assertEqual(httpretty.last_request().body, json.dumps({
            'user_id': self.user.id,
            'expires_at': twenty_four_hrs_later.isoformat(),
        }))
        auth_header = 'Token {api_key}'.format(api_key=settings.METEOR_KEY)
        self.assertEqual(httpretty.last_request().headers['Authorization'],
                         auth_header)
        self.assertEqual(httpretty.last_request().headers['Content-Type'],
                         'application/json')

    @httpretty.activate
    def test_add_members_bad_response(self):
        # Mock a bad response from the meteor server.
        httpretty.register_uri(httpretty.POST, self.add_members_url,
                               status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        with self.assertRaises(requests.exceptions.HTTPError):
            add_members(self.event, self.user.id)
