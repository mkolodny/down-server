# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0038_auto_20150905_1859'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='bulk_ref',
            field=models.TextField(db_index=True, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='userphone',
            name='bulk_ref',
            field=models.TextField(db_index=True, null=True, blank=True),
        ),
    ]
