# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0037_auto_20150815_1638'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invitation',
            name='last_viewed',
        ),
    ]
