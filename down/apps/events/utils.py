from __future__ import unicode_literals
import json
from django.conf import settings
import requests


def add_member(group_id, user_id):
    url = '{meteor_url}/groups/{group_id}/members'.format(
            meteor_url=settings.METEOR_URL, group_id=group_id)
    data = json.dumps({
        'user_id': user_id,
    })
    auth_header = 'Token {api_key}'.format(api_key=settings.METEOR_KEY)
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json',
    }
    response = requests.post(url, data=data, headers=headers)
    response.raise_for_status()

def remove_member(group_id, user):
    url = '{meteor_url}/groups/{group_id}/members/{user_id}'.format(
            meteor_url=settings.METEOR_URL, group_id=group_id, user_id=user.id)
    data = json.dumps({
        'member': {
            'name': user.name,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'image_url': user.image_url,
        },
    })
    headers = {
        'Authorization': 'Token {api_key}'.format(api_key=settings.METEOR_KEY),
        'Content-Type': 'application/json',
    }
    response = requests.delete(url, data=data, headers=headers)
    response.raise_for_status()
