# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0005_auto_20150308_2325'),
    ]

    operations = [
        migrations.RenameField(
            model_name='invitation',
            old_name='datetime_sent',
            new_name='created_at',
        ),
    ]
