# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0017_event_last_updated'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='previously_accepted',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
