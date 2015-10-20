# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0032_auto_20150706_1716'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invitation',
            name='response',
            field=models.SmallIntegerField(default=0, choices=[(0, 'no response'), (1, 'accepted'), (2, 'declined'), (3, 'maybe')]),
            preserve_default=True,
        ),
    ]
