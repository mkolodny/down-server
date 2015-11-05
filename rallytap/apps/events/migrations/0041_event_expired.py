# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0040_remove_invitation_previously_accepted'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='expired',
            field=models.BooleanField(default=False),
        ),
    ]
