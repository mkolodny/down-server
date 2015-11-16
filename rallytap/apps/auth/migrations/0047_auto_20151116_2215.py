# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0046_auto_20151116_2214'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Groups',
            new_name='Group',
        ),
    ]
