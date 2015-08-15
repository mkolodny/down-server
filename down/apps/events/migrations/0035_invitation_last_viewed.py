# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0034_event_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='last_viewed',
            field=models.DateTimeField(default=datetime.datetime(2015, 8, 15, 16, 33, 17, 79470, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
    ]
