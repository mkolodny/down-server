# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0019_auto_20150328_2136'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='authtoken',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='firebase_token',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
