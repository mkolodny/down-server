# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0040_user_is_staff'),
    ]

    operations = [
        migrations.CreateModel(
            name='FellowshipApplication',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.TextField()),
                ('school', models.TextField()),
            ],
        ),
    ]
