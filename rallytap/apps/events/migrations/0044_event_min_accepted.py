# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0043_remove_event_canceled'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='min_accepted',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
    ]
