# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0015_remove_invitation_previously_accepted'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='last_updated',
            field=models.DateTimeField(default=datetime.datetime(2015, 4, 20, 6, 21, 26, 834931, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
    ]
