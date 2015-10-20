# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0023_user_added_me'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='added_me',
        ),
    ]
