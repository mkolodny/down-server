# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0005_auto_20150402_2203'),
    ]

    operations = [
        migrations.AlterField(
            model_name='friendship',
            name='friend',
            field=models.ForeignKey(related_name='friend+', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='friendship',
            name='user',
            field=models.ForeignKey(related_name='user+', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
