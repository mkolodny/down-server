# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0012_auto_20150309_1516'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='notify_token',
        ),
    ]
