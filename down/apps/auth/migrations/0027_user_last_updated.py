# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0026_remove_user_facebook_friends'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='last_updated',
            field=models.DateTimeField(default=datetime.datetime(2015, 4, 20, 14, 47, 17, 936438, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
    ]
