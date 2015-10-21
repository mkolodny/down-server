# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
from rallytap.apps.utils.utils import add_members


def befriend_teamrallytap(apps, schema_editor):
    if settings.ENV == 'dev':
        return

    User = apps.get_model('down_auth', 'User')
    Friendship = apps.get_model('friends', 'Friendship')
    teamrallytap = User.objects.get(username='teamrallytap')
    friendships = []
    for user in User.objects.all().exclude(id=teamrallytap.id):
        # Make the user friends with Team Rallytap.
        friendship.append(Friendship(user=user, friend=teamrallytap))
        friendship.append(Friendship(user=teamrallytap, friend=user))
    friendships.bulk_create(friendships)

class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0016_remove_friendship_was_acknowledged'),
    ]

    operations = [
        migrations.RunPython(befriend_teamrallytap),
    ]
