# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0023_allfriendsinvitation'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='open',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
