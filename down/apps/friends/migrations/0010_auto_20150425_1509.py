# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0009_friendship_last_updated'),
    ]

    operations = [
        migrations.RenameField(
            model_name='friendship',
            old_name='last_updated',
            new_name='updated_at',
        ),
    ]
