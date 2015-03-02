# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0006_remove_user_firebase_token'),
    ]

    operations = [
        migrations.RenameField(
            model_name='socialaccount',
            old_name='provided_data',
            new_name='profile',
        ),
    ]
