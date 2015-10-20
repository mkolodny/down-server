# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0036_remove_invitation_open'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='allfriendsinvitation',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='allfriendsinvitation',
            name='event',
        ),
        migrations.RemoveField(
            model_name='allfriendsinvitation',
            name='from_user',
        ),
        migrations.DeleteModel(
            name='AllFriendsInvitation',
        ),
    ]
