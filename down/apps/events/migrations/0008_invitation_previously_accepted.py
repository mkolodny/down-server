# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0007_auto_20150309_1515'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='previously_accepted',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
