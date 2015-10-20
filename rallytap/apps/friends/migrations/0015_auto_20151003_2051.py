# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models, migrations
from rallytap.apps.utils.utils import add_members


def add_friend_chat_members(apps, schema_editor):
    Friendship = apps.get_model('friends', 'Friendship')
    for friendship in Friendship.objects.all():
        user_id = friendship.user_id
        friend_id = friendship.friend_id
        chat_id = '{user_id},{friend_id}'.format(user_id=user_id, friend_id=friend_id)
        user_ids = [user_id, friend_id]
        add_members(chat_id, user_ids)


class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0014_auto_20150924_2011'),
    ]

    operations = [
        migrations.RunPython(add_friend_chat_members),
    ]
