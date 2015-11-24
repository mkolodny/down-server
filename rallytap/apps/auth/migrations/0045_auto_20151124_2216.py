# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def reset_negative_points(apps, schema_editor):
    User = apps.get_model('down_auth', 'User')
    User.objects.filter(points__lt=100).update(points=100)
        
class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0044_auto_20151109_2045'),
    ]

    operations = [
        migrations.RunPython(reset_negative_points),
    ]
