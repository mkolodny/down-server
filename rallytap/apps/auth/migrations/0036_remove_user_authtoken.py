# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0035_auto_20150811_1605'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='authtoken',
        ),
    ]
