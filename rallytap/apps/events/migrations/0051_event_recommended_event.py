# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0050_auto_20151202_1916'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='recommended_event',
            field=models.ForeignKey(blank=True, to='events.RecommendedEvent', null=True),
        ),
    ]
