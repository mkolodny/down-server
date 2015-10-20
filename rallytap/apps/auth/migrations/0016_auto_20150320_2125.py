# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0015_linfootfunnel'),
    ]

    operations = [
        migrations.AlterField(
            model_name='linfootfunnel',
            name='phone',
            field=phonenumber_field.modelfields.PhoneNumberField(unique=True, max_length=128),
            preserve_default=True,
        ),
    ]
