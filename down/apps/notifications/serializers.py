from __future__ import unicode_literals
from binascii import a2b_base64, b2a_hex
import re
from rest_framework import serializers
from push_notifications.models import APNSDevice


class APNSDeviceSerializer(serializers.ModelSerializer):

    class Meta:
        model = APNSDevice

    def create(self, validated_data):
        """
        Re-encode the APNS device token from base64 to hex. We need to do this
        because we're sending back base64 from the client right now with
        deviceToken.base64EncodedStringWithOptions(nil). Once we update the client
        to use deviceToken.description, we can remove this.
        """
        base64_registration_id = validated_data['registration_id']
        hex_registration_id = b2a_hex(a2b_base64(base64_registration_id))
        validated_data['registration_id'] = hex_registration_id

        return super(APNSDeviceSerializer, self).create(validated_data)
