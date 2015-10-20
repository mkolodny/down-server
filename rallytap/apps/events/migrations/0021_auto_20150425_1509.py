# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0020_auto_20150423_0145'),
    ]

    operations = [
        migrations.RenameField(
            model_name='event',
            old_name='last_updated',
            new_name='updated_at',
        ),
        migrations.RenameField(
            model_name='invitation',
            old_name='last_updated',
            new_name='updated_at',
        ),
    ]
