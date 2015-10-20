# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0007_auto_20150302_0330'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='firebase_token',
            field=models.TextField(unique=True, null=True),
            preserve_default=True,
        ),
    ]
