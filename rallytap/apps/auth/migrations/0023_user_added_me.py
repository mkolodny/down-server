# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0007_auto_20150403_2003'),
        ('down_auth', '0022_remove_user_friend_requests'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='added_me',
            field=models.ManyToManyField(related_name='related_added_me+', through='friends.AddedMe', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
