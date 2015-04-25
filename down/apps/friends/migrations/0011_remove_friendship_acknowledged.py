# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0010_auto_20150425_1509'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='friendship',
            name='acknowledged',
        ),
    ]
