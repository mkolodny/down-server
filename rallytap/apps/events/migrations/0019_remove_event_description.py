# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0018_invitation_previously_accepted'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='description',
        ),
    ]
