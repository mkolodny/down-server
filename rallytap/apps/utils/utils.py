from __future__ import unicode_literals
from datetime import timedelta
import json
from django.conf import settings
import requests


def add_members(event, user_id):
    url = '{meteor_url}/events/{event_id}/members'.format(
            meteor_url=settings.METEOR_URL, event_id=event.id)
    if event.datetime is not None:
        twenty_four_hrs_later = event.datetime + timedelta(hours=24)
    else:
        twenty_four_hrs_later = event.created_at + timedelta(hours=24)
    data = json.dumps({
        'user_id': user_id,
        'expires_at': twenty_four_hrs_later.isoformat(),
    })
    auth_header = 'Token {api_key}'.format(api_key=settings.METEOR_KEY)
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json',
    }
    response = requests.post(url, data=data, headers=headers)
    response.raise_for_status()
