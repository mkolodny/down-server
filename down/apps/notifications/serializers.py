from __future__ import unicode_literals
import re
from rest_framework import serializers
from push_notifications.models import APNSDevice


class APNSDeviceSerializer(serializers.ModelSerializer):

    class Meta:
        model = APNSDevice
