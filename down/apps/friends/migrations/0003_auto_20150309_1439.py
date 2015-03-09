# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0002_auto_20150302_2051'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='friendship',
            unique_together=set([('user1', 'user2')]),
        ),
    ]
