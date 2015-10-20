# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0004_auto_20150302_0040'),
    ]

    operations = [
        migrations.AlterField(
            model_name='socialaccount',
            name='uid',
            field=models.TextField(db_index=True),
            preserve_default=True,
        ),
    ]
