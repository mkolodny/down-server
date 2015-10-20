# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0003_auto_20150302_0858'),
    ]

    operations = [
        migrations.AlterField(
            model_name='place',
            name='geo',
            field=django.contrib.gis.db.models.fields.PointField(srid=4326, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='place',
            name='name',
            field=models.TextField(default='Bars?!?!?!'),
            preserve_default=False,
        ),
    ]
