# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0004_auto_20150309_1515'),
    ]

    operations = [
        migrations.RenameField(
            model_name='friendship',
            old_name='user1',
            new_name='user',
        ),
        migrations.RenameField(
            model_name='friendship',
            old_name='user2',
            new_name='friend',
        ),
        migrations.AlterUniqueTogether(
            name='friendship',
            unique_together=set([('user', 'friend')]),
        ),
    ]
