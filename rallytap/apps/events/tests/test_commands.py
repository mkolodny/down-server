from __future__ import unicode_literals
from datetime import datetime, timedelta
import json
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
import httpretty
import pytz
from rallytap.apps.auth.models import User
from rallytap.apps.events.models import Event


class ExpireEventsTests(TestCase):

    def setUp(self):
        self.user = User()
        self.user.save()
        self.event = Event(creator=self.user, title='drop it like it\'s hot')
        self.event.save()

        # Save URLs.
        self.url = '{meteor_url}/chats/expire'.format(
                meteor_url=settings.METEOR_URL)

    @httpretty.activate
    def test_expired_no_datetime(self):
        # Mock the response from the meteor server.
        httpretty.register_uri(httpretty.POST, self.url)

        # Mock an expired event without a datetime (by default, events expire after
        # 24 hours).
        self.event.created_at = datetime.now(pytz.utc) - timedelta(hours=24)
        self.event.save()

        call_command('expireevents')

        # It should mark the event as expired.
        # Workaround for comparing a dict with a list as a value.
        last_request = httpretty.last_request()
        data = {'ids': [self.event.id]}
        self.assertEqual(last_request.body, json.dumps(data))
        self.assertEqual(last_request.headers['Content-Type'], 'application/json')
        auth_header = 'Token {api_key}'.format(api_key=settings.METEOR_KEY)
        self.assertEqual(last_request.headers['Authorization'], auth_header)

    @httpretty.activate
    def test_expired_has_datetime(self):
        # Mock the response from the meteor server.
        httpretty.register_uri(httpretty.POST, self.url)

        # Mock an expired event with a datetime.
        self.event.datetime = datetime.now(pytz.utc) - timedelta(hours=24)
        self.event.save()

        call_command('expireevents')

        # It should mark the event as expired.
        # Workaround for comparing a dict with a list as a value.
        last_request = httpretty.last_request()
        data = {'ids': [self.event.id]}
        self.assertEqual(last_request.body, json.dumps(data))
        self.assertEqual(last_request.headers['Content-Type'], 'application/json')
        auth_header = 'Token {api_key}'.format(api_key=settings.METEOR_KEY)
        self.assertEqual(last_request.headers['Authorization'], auth_header)
