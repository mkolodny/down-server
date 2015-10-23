# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def remove_duplicate_apnsdevices(apps, schema_editor):
    devices = {}

    APNSDevice = apps.get_model('push_notifications', 'APNSDevice')
    for apnsdevice in APNSDevice.objects.all():
        if apnsdevice.device_id not in devices:
            devices[apnsdevice.device_id] = apnsdevice
            continue

        # An APNSDevice already exists with the given device id. So delete the
        # APNSDevice with the lower id, and set the other APNSDevice on the
        # dict of devices.
        previous_apnsdevice = devices[apnsdevice.device_id]
        if previous_apnsdevice.id > apnsdevice.id:
            remove_device = apnsdevice
            current_device = previous_apnsdevice
        else:
            remove_device = previous_apnsdevice
            current_device = apnsdevice
        remove_device.delete()
        devices[apnsdevice.device_id] = current_device

class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0008_auto_20151016_2313'),
    ]

    operations = [
        migrations.RunPython(remove_duplicate_apnsdevices),
    ]
