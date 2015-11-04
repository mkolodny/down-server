# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations


def befriend_teamrallytap(apps, schema_editor):
    if settings.ENV == 'dev':
        return

    User = apps.get_model('down_auth', 'User')
    Friendship = apps.get_model('friends', 'Friendship')
    teamrallytap = User.objects.get(username='teamrallytap')
    friendships = []
    for user in User.objects.exclude(id=teamrallytap.id):
        try:
            Friendship.objects.get(user=teamrallytap, friend=user)
        except Friendship.DoesNotExist:
            friendships.append(Friendship(user=teamrallytap, friend=user))
            friendships.append(Friendship(user=user, friend=teamrallytap))
    Friendship.objects.bulk_create(friendships)

class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0020_auto_20151022_1928'),
    ]

    operations = [
        migrations.RunPython(befriend_teamrallytap),
    ]
