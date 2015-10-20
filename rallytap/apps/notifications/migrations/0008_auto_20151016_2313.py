# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0007_auto_20151014_1919'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='friendselectpushnotification',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='friendselectpushnotification',
            name='friend',
        ),
        migrations.RemoveField(
            model_name='friendselectpushnotification',
            name='user',
        ),
        migrations.DeleteModel(
            name='FriendSelectPushNotification',
        ),
    ]
