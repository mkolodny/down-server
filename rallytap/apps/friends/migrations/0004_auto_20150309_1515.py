# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0003_auto_20150309_1439'),
    ]

    operations = [
        migrations.AlterField(
            model_name='friendrequests',
            name='from_user',
            field=models.ForeignKey(related_name='from_users', to='down_auth.User'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='friendrequests',
            name='to_user',
            field=models.ForeignKey(related_name='to_users', to='down_auth.User'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='friendship',
            name='user1',
            field=models.ForeignKey(related_name='friend1s+', to='down_auth.User'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='friendship',
            name='user2',
            field=models.ForeignKey(related_name='friend2s+', to='down_auth.User'),
            preserve_default=True,
        ),
    ]
