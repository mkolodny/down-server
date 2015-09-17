# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0033_auto_20150708_2151'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='comment',
            field=models.TextField(null=True, blank=True),
        ),
    ]
