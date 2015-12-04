from __future__ import unicode_literals
from datetime import datetime, timedelta
import json
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
import pytz
from rallytap.apps.auth.models import Points, User
from rallytap.apps.events.models import Event
from rallytap.apps.utils.exceptions import ServiceUnavailable


class ExpireEventsTests(TestCase):

    def setUp(self):
        self.user = User()
        self.user.save()
        self.event = Event(creator=self.user, title='drop it like it\'s hot')
        self.event.save()

    def test_expired_no_datetime(self):
        # Mock an expired event without a datetime (by default, events expire after
        # 12 hours).
        self.event.created_at = datetime.now(pytz.utc) - timedelta(hours=12)
        self.event.save()

        call_command('expireevents')

        # It should update the event.
        event = Event.objects.get(id=self.event.id)
        self.assertEqual(event.expired, True)

    def test_expired_has_datetime(self):
        # Mock an expired event with a datetime.
        self.event.datetime = datetime.now(pytz.utc) - timedelta(hours=12)
        self.event.save()

        call_command('expireevents')

        # It should update the event.
        event = Event.objects.get(id=self.event.id)
        self.assertEqual(event.expired, True)
