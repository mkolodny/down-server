# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0011_auto_20150419_1426'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='status',
            field=models.SmallIntegerField(default=0, choices=[(0, 'no response'), (1, 'accepted'), (2, 'declined')]),
            preserve_default=True,
        ),
    ]
