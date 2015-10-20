# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='firebaseToken',
            new_name='firebase_token',
        ),
        migrations.RenameField(
            model_name='user',
            old_name='notifyToken',
            new_name='notify_token',
        ),
    ]
