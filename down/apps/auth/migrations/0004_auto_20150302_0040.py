# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0001_initial'),
        ('down_auth', '0003_auto_20150301_2212'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='friend_requests',
            field=models.ManyToManyField(related_name='user_friend_requests', through='friends.FriendRequests', to='down_auth.User'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='friends',
            field=models.ManyToManyField(related_name='user_friends', through='friends.Friend', to='down_auth.User'),
            preserve_default=True,
        ),
    ]
