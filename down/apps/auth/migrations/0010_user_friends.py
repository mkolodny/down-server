# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0002_auto_20150302_2051'),
        ('down_auth', '0009_remove_user_friends'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='friends',
            field=models.ManyToManyField(related_name='user_friends', through='friends.Friendship', to='down_auth.User'),
            preserve_default=True,
        ),
    ]
