# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0008_auto_20150403_2007'),
    ]

    operations = [
        migrations.AddField(
            model_name='friendship',
            name='last_updated',
            field=models.DateTimeField(default=datetime.datetime(2015, 4, 20, 14, 47, 37, 758876, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
    ]
