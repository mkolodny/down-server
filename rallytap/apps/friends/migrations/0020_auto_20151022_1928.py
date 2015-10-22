# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from django.db import models, migrations
from django.conf import settings
import requests
from rallytap.apps.utils.utils import add_members


def create_chats(chats):
    # Create the chats.
    url = '{meteor_url}/chats/members'.format(meteor_url=settings.METEOR_URL)
    data = json.dumps({'chats': chats})
    auth_header = 'Token {api_key}'.format(api_key=settings.METEOR_KEY)
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json',
    }
    response = requests.post(url, data=data, headers=headers)
    response.raise_for_status()

def create_teamrallytap_chats(apps, schema_editor):
    if settings.ENV == 'dev':
        return

    User = apps.get_model('down_auth', 'User')
    teamrallytap = User.objects.get(username='teamrallytap')
    chats = []
    i = 0
    for user in User.objects.all().exclude(id=teamrallytap.id):
        chat_id = '{user_id},{team_id}'.format(user_id=user.id,
                                               team_id=teamrallytap.id)
        chats.append({'chat_id': chat_id, 'user_ids': [user.id, teamrallytap.id]})

        if i < 1000:
            i += 1
            continue

        create_chats(chats)

        # Reset
        chats = []
        i = 0

    # Create any remaining chats.
    if len(chats) > 0:
        create_chats(chats)

class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0019_auto_20151021_2008'),
    ]

    operations = [
        migrations.RunPython(create_teamrallytap_chats),
    ]
