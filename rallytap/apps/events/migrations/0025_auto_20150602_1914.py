# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0024_invitation_open'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='allfriendsinvitation',
            unique_together=set([('event', 'from_user')]),
        ),
    ]
