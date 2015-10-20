# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0024_remove_user_added_me'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='socialaccount',
            unique_together=set([('provider', 'uid')]),
        ),
    ]
