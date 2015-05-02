# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def clear_friendships(apps, schema_editor):
    Friendship = apps.get_model('friends', 'Friendship')
    Friendship.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0011_remove_friendship_acknowledged'),
    ]

    operations = [
        migrations.RunPython(clear_friendships),
    ]
