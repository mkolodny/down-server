# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0003_auto_20151014_1825'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='friendselectpushnotification',
            unique_together=set([('user', 'friend')]),
        ),
    ]
