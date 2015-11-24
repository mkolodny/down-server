# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0048_savedevent'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='friends_only',
            field=models.BooleanField(default=False),
        ),
    ]
