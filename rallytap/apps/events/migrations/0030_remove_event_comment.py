# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0029_auto_20150706_0510'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='comment',
        ),
    ]
