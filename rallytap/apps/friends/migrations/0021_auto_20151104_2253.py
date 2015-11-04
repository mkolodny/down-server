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
    user_ids = User.objects.exclude(id=teamrallytap.id).values_list('id', flat=True)
    friendships = []

    # Create friendships from teamrallytap for users who haven't been added by
    # teamrallytap yet.
    tr_friendships = Friendship.objects.filter(user=teamrallytap, friend=user)
    tr_users = {friendship.friend_id for friendship in friendships}
    no_tr_users = [user_id for user_id in user_ids if user_id not in tr_users]
    for user_id in no_tr_users:
        friendships.append(Friendship(user=teamrallytap, friend_id=user_id))

    # Create friendships from teamrallytap for users who haven't added
    # teamrallytap yet.
    user_friendships = Friendship.objects.filter(user=user, friend=teamrallytap)
    users = {friendship.user_id for friendship in friendships}
    no_users = [user_id for user_id in user_ids if user_id not in users]
    for user_id in no_users:
        friendships.append(Friendship(user=user_id, friend_id=teamrallytap))

    Friendship.objects.bulk_create(friendships)

class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0020_auto_20151022_1928'),
    ]

    operations = [
        migrations.RunPython(befriend_teamrallytap),
    ]
