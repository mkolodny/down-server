# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0025_auto_20150406_0449'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='facebook_friends',
        ),
    ]
