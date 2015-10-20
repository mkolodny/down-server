# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0039_remove_invitation_to_user_messaged'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invitation',
            name='previously_accepted',
        ),
    ]
