# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0005_auto_20150302_0256'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='firebase_token',
        ),
    ]
