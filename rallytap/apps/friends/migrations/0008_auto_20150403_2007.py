# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0024_remove_user_added_me'),
        ('friends', '0007_auto_20150403_2003'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='addedme',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='addedme',
            name='added_by',
        ),
        migrations.RemoveField(
            model_name='addedme',
            name='user',
        ),
        migrations.DeleteModel(
            name='AddedMe',
        ),
        migrations.AddField(
            model_name='friendship',
            name='acknowledged',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
