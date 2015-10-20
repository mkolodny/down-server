# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0011_auto_20150309_1515'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='friend_requests',
            field=models.ManyToManyField(related_name='related_friend_requests+', through='friends.FriendRequests', to='down_auth.User'),
            preserve_default=True,
        ),
    ]
