# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0025_auto_20150602_1914'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='to_user_messaged',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
