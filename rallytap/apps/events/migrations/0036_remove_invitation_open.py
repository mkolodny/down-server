# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0035_invitation_last_viewed'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invitation',
            name='open',
        ),
    ]
