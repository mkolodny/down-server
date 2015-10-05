from __future__ import unicode_literals
import json
from django.conf import settings
import requests


def add_members(chat_id, user_ids):
    url = '{meteor_url}/chats/{chat_id}/members'.format(
            meteor_url=settings.METEOR_URL, chat_id=chat_id)
    data = json.dumps({
        'user_ids': user_ids,
    })
    auth_header = 'Token {api_key}'.format(api_key=settings.METEOR_KEY)
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json',
    }
    response = requests.post(url, data=data, headers=headers)
    response.raise_for_status()

def remove_member(chat_id, user):
    url = '{meteor_url}/chats/{chat_id}/members/{user_id}'.format(
            meteor_url=settings.METEOR_URL, chat_id=chat_id, user_id=user.id)
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