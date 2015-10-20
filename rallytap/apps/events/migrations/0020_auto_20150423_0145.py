# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0019_remove_event_description'),
    ]

    operations = [
        migrations.RenameField(
            model_name='invitation',
            old_name='status',
            new_name='response',
        ),
    ]
