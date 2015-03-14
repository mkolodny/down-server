# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from binascii import a2b_base64, b2a_hex


def base64_to_hex(apps, schema_editor):
    """
    Convert users' device tokens from base 64 to hex.
    """
    APNSDevice = apps.get_model('push_notifications', 'APNSDevice')
    for device in APNSDevice.objects.all():
        device.registration_id = b2a_hex(a2b_base64(device.registration_id))
        device.save()
        

class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0013_remove_user_notify_token'),
        # Add dependency to use APNSDevice.
        ('push_notifications', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(base64_to_hex)
    ]
