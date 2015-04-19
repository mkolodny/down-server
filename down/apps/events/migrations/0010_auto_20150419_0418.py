# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0009_auto_20150419_0340'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invitation',
            name='from_user',
            field=models.ForeignKey(related_name='related_from_user+', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
