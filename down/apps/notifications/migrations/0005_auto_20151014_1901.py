# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0004_auto_20151014_1854'),
    ]

    operations = [
        migrations.RenameField(
            model_name='friendselectpushnotification',
            old_name='lastest_sent_at',
            new_name='latest_sent_at',
        ),
    ]
