# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0021_user_facebook_friends'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='friend_requests',
        ),
    ]
