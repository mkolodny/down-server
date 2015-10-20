# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0006_auto_20151014_1915'),
    ]

    operations = [
        migrations.AlterField(
            model_name='friendselectpushnotification',
            name='latest_sent_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
