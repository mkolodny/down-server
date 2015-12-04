# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0047_auto_20151202_2012'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='last_posted',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
