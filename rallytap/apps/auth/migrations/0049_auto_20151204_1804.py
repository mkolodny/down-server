# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0048_user_last_posted'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='last_posted',
            new_name='last_post_notification',
        ),
    ]
