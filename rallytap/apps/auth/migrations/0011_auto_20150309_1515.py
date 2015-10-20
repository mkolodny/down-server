# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0010_user_friends'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='friend_requests',
            field=models.ManyToManyField(to='down_auth.User', through='friends.FriendRequests'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='friends',
            field=models.ManyToManyField(related_name='related_friends+', through='friends.Friendship', to='down_auth.User'),
            preserve_default=True,
        ),
    ]
