# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0004_auto_20150302_0040'),
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='members',
            field=models.ManyToManyField(to='down_auth.User', through='events.Invitation'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='event',
            name='creator',
            field=models.ForeignKey(related_name='event_creator', to='down_auth.User'),
            preserve_default=True,
        ),
    ]
