# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0049_event_friends_only'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='savedevent',
            unique_together=set([('user', 'event')]),
        ),
    ]
