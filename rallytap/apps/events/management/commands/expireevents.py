from __future__ import unicode_literals
from datetime import datetime, timedelta
import json
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import F, Q
import pytz
import requests
from rallytap.apps.auth.models import Points, User
from rallytap.apps.events.models import Event
from rallytap.apps.utils.exceptions import ServiceUnavailable


class Command(BaseCommand):
    help = 'Marks expired events as expired on the Meteor server.'

    def handle(self, *args, **options):
        twenty_four_hrs_ago = datetime.now(pytz.utc) - timedelta(hours=24)
        event_ids = Event.objects.filter(
                        Q(datetime__isnull=True,
                          created_at__lte=twenty_four_hrs_ago) |
                        Q(datetime__isnull=False,
                          datetime__lte=twenty_four_hrs_ago),
                        expired=False) \
                .values_list('id', flat=True)

        # Expire the events on the meteor server.
        url = '{meteor_url}/chats/expire'.format(meteor_url=settings.METEOR_URL)
        data = {'ids': list(event_ids)}
        auth_header = 'Token {api_key}'.format(api_key=settings.METEOR_KEY)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': auth_header,
        }
        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code != 200:
            raise ServiceUnavailable()

        # Set the events to expired in the DB.
        Event.objects.filter(id__in=event_ids).update(expired=True)
