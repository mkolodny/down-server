# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0016_invitation_last_updated'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='last_updated',
            field=models.DateTimeField(default=datetime.datetime(2015, 4, 20, 14, 47, 35, 182710, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
    ]
