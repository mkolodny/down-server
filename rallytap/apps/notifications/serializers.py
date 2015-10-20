from __future__ import unicode_literals
from binascii import a2b_base64, b2a_hex
import re
from rest_framework import serializers, fields
from push_notifications.models import APNSDevice, GCMDevice


class APNSDeviceSerializer(serializers.ModelSerializer):

    class Meta:
        model = APNSDevice


class HexIntegerField(fields.IntegerField):
    """
    Store an integer represented as a hex string of form "0x01".
    """

    def to_internal_value(self, data):
        data = int(data, 16)
        return super(HexIntegerField, self).to_internal_value(data)

    def to_representation(self, value):
        return value


class GCMDeviceSerializer(serializers.ModelSerializer):
    device_id = HexIntegerField(
        help_text='ANDROID_ID / TelephonyManager.getDeviceId() (e.g: 0x01)',
    )

    class Meta:
        model = GCMDevice
