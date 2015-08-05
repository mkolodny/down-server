from __future__ import unicode_literals
import json
from django.conf import settings
import requests


def add_member(event_id, user_id):
    url = '{meteor_url}/events/{event_id}/members'.format(
            meteor_url=settings.METEOR_URL, event_id=event_id)
    data = json.dumps({
        'user_id': user_id,
    })
    response = requests.post(url, data=data)
    response.raise_for_status()

def remove_member(event_id, user_id):
    url = '{meteor_url}/events/{event_id}/members/{user_id}'.format(
            meteor_url=settings.METEOR_URL, event_id=event_id, user_id=user_id)
    response = requests.delete(url)
    response.raise_for_status()
