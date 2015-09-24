# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def set_was_acknowledged(apps, schema_editor):
    Friendship = apps.get_model('friends', 'Friendship')
    for friendship in Friendship.objects.all():
        try:
            # Check if the user's friend has added the user back.
            friendship = Friendship.objects.get(user_id=friendship.friend_id,
                                                friend_id=friendship.user_id)
            friendship.was_acknowledged = True
            friendship.save()
        except Friendship.DoesNotExist:
            # Keep the friendship as not acknowledged.
            continue

class Migration(migrations.Migration):

    dependencies = [
        ('friends', '0012_auto_20150502_2006'),
    ]

    operations = [
        migrations.AddField(
            model_name='friendship',
            name='was_acknowledged',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
        migrations.RunPython(set_was_acknowledged),
    ]
