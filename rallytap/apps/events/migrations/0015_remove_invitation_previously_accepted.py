# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0014_auto_20150420_0604'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invitation',
            name='previously_accepted',
        ),
    ]
