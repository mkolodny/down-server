# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0026_invitation_to_user_messaged'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='muted',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
