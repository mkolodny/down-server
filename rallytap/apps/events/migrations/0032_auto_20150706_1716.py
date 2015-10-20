# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0031_auto_20150706_1641'),
    ]

    operations = [
        migrations.AlterField(
            model_name='linkinvitation',
            name='link_id',
            field=models.TextField(unique=True),
            preserve_default=True,
        ),
    ]
