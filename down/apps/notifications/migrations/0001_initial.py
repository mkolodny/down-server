# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def clear_apns_devices(apps, schema_editor):
    APNSDevice = apps.get_model('push_notifications', 'APNSDevice')
    APNSDevice.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.RunPython(clear_apns_devices),
    ]
