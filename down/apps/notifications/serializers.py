from __future__ import unicode_literals
import re
from rest_framework import serializers
from push_notifications.models import APNSDevice

HEX64_RE = re.compile('[0-9a-f]{64}', re.IGNORECASE)


class APNSDeviceSerializer(serializers.ModelSerializer):

	class Meta:
		model = APNSDevice

        def validate_registration_id(self, value):
            '''
            Make sure the iOS device token is a 256-bit hexadecimal (64
            characters).
            '''
            if HEX64_RE.match(value) is None:
                raise serializers.ValidationError('Registration ID (device token)'
                                                  'is invalid')
            return value
