from __future__ import unicode_literals
from datetime import datetime, timedelta
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
import mock
import pytz
from rallytap.apps.auth.models import User
from rallytap.apps.events.models import Event


class ExpireEventsTests(TestCase):

    def setUp(self):
        self.user = User()
        self.user.save()
        self.event = Event(creator=self.user, title='drop it like it\'s hot')
        self.event.save()

    @mock.patch('rallytap.apps.events.management.commands.expireevents.requests')
    def test_expired_no_datetime(self, mock_requests):
        # Mock an expired event without a datetime (by default, events expire after
        # 24 hours).
        self.event.created_at = datetime.now(pytz.utc) - timedelta(hours=24)
        self.event.save()

        call_command('expireevents')

        # It should mark the event as expired.
        url = '{meteor_url}/chats'.format(meteor_url=settings.METEOR_URL)
        data = {'chat_ids': [self.event.id]}
        # Workaround for comparing a dict with a list as a value.
        self.assertEqual(mock_requests.delete.call_count, 1)
        self.assertEqual(mock_requests.delete.call_args[0][0], url)
        self.assertItemsEqual(mock_requests.delete.call_args[1], {'data': None})
        self.assertItemsEqual(mock_requests.delete.call_args[1]['data'],
                              {'chat_ids': None})
        self.assertSequenceEqual(
                mock_requests.delete.call_args[1]['data']['chat_ids'],
                [self.event.id])

    @mock.patch('rallytap.apps.events.management.commands.expireevents.requests')
    def test_expired_has_datetime(self, mock_requests):
        # Mock an expired event with a datetime.
        self.event.datetime = datetime.now(pytz.utc) - timedelta(hours=24)
        self.event.save()

        call_command('expireevents')

        # It should mark the event as expired.
        url = '{meteor_url}/chats'.format(meteor_url=settings.METEOR_URL)
        data = {'chat_ids': [self.event.id]}
        # Workaround for comparing a dict with a list as a value.
        self.assertEqual(mock_requests.delete.call_count, 1)
        self.assertEqual(mock_requests.delete.call_args[0][0], url)
        self.assertItemsEqual(mock_requests.delete.call_args[1], {'data': None})
        self.assertItemsEqual(mock_requests.delete.call_args[1]['data'],
                              {'chat_ids': None})
        self.assertSequenceEqual(
                mock_requests.delete.call_args[1]['data']['chat_ids'],
                [self.event.id])
