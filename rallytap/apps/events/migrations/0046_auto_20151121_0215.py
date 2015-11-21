# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0045_remove_event_min_accepted'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='invitation',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='invitation',
            name='event',
        ),
        migrations.RemoveField(
            model_name='invitation',
            name='from_user',
        ),
        migrations.RemoveField(
            model_name='invitation',
            name='to_user',
        ),
        migrations.AlterUniqueTogether(
            name='linkinvitation',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='linkinvitation',
            name='event',
        ),
        migrations.RemoveField(
            model_name='linkinvitation',
            name='from_user',
        ),
        migrations.RemoveField(
            model_name='event',
            name='members',
        ),
        migrations.DeleteModel(
            name='Invitation',
        ),
        migrations.DeleteModel(
            name='LinkInvitation',
        ),
    ]
