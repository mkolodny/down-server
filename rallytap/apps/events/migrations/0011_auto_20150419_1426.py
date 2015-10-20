# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0010_auto_20150419_0418'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='invitation',
            unique_together=set([('to_user', 'event')]),
        ),
    ]
