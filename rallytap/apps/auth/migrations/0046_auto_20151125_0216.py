# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def create_meteor_user(apps, schema_editor):
    User = apps.get_model('down_auth', 'User')
    user = User(id=-1)
    user.save()
        
class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0045_auto_20151124_2216'),
    ]

    operations = [
        migrations.RunPython(create_meteor_user),
    ]
