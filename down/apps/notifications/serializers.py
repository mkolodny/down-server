from __future__ import unicode_literals
from binascii import a2b_base64, b2a_hex
import re
from rest_framework import serializers
from push_notifications.models import APNSDevice


class APNSDeviceSerializer(serializers.ModelSerializer):

    class Meta:
        model = APNSDevice
