# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0013_friendship_was_acknowledged'),
    ]

    operations = [
        migrations.AlterField(
            model_name='friendship',
            name='was_acknowledged',
            field=models.BooleanField(default=False),
        ),
    ]
