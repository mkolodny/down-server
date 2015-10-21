# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
from rallytap.apps.utils.utils import add_members


def teamrallytap(apps, schema_editor):
    if settings.ENV == 'dev':
        return

    User = apps.get_model('down_auth', 'User')
    Friendship = apps.get_model('friends', 'Friendship')
    teamrallytap = User.objects.get(username='teamrallytap')
    for user in User.objects.all().exclude(id=teamrallytap.id):
        # Create a chat on the Meteor server.
        chat_id = '{user_id},{friend_id}'.format(user_id=user.id,
                                                 friend_id=teamrallytap.id)
        user_ids = [user.id, teamrallytap.id]
        add_members(chat_id, user_ids)

class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0017_auto_20151021_0342'),
    ]

    operations = [
        migrations.RunPython(teamrallytap),
    ]
