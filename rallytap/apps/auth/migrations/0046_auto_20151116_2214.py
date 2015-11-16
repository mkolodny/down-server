# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0045_groups'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groups',
            name='domain',
            field=models.TextField(unique=True),
        ),
    ]
