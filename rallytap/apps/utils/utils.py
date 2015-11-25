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
