# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0027_user_last_updated'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='last_updated',
            new_name='updated_at',
        ),
    ]
