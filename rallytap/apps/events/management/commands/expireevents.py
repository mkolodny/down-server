from __future__ import unicode_literals
from datetime import datetime, timedelta
import json
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
import pytz
import requests
from rallytap.apps.events.models import Event


class Command(BaseCommand):
    help = 'Marks expired events as expired on the Meteor server.'

    def handle(self, *args, **options):
        twenty_four_hrs_ago = datetime.now(pytz.utc) - timedelta(hours=24)
        event_ids = Event.objects.filter(
                        Q(datetime__isnull=True,
                          created_at__lte=twenty_four_hrs_ago) |
                        Q(datetime__isnull=False,
                          datetime__lte=twenty_four_hrs_ago)) \
                .values_list('id', flat=True)
        url = '{meteor_url}/chats/expire'.format(meteor_url=settings.METEOR_URL)
        data = {'ids': list(event_ids)}
        auth_header = 'Token {api_key}'.format(api_key=settings.METEOR_KEY)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': auth_header,
        }
        requests.post(url, data=json.dumps(data), headers=headers)
