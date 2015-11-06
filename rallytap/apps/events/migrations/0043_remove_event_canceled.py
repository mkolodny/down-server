# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0042_remove_event_comment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='canceled',
        ),
    ]
