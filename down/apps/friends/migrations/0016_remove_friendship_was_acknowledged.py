# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0015_auto_20151003_2051'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='friendship',
            name='was_acknowledged',
        ),
    ]
