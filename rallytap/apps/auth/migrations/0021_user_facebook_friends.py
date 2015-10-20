# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0020_auto_20150328_2238'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='facebook_friends',
            field=models.ManyToManyField(related_name='related_facebook_friends+', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
