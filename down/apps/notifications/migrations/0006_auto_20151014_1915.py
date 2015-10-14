# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0005_auto_20151014_1901'),
    ]

    operations = [
        migrations.AlterField(
            model_name='friendselectpushnotification',
            name='latest_sent_at',
            field=models.DateTimeField(),
        ),
    ]
