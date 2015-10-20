# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0016_auto_20150320_2125'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.TextField()),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(unique=True, max_length=128)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
