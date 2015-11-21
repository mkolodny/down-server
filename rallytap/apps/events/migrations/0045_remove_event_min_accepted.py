# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0044_event_min_accepted'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='min_accepted',
        ),
    ]
