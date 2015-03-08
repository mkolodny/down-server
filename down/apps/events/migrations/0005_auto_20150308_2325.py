# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0004_auto_20150304_0346'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='place',
            field=models.ForeignKey(blank=True, to='events.Place', null=True),
            preserve_default=True,
        ),
    ]
