from __future__ import unicode_literals
from binascii import a2b_base64, b2a_hex
from django.core.urlresolvers import reverse
from django.test import TestCase
from push_notifications.models import APNSDevice
from rest_framework import status
from rest_framework.test import APITestCase
from down.apps.auth.models import User


class APNSDeviceTests(APITestCase):

    def setUp(self):
        # Mock a user.
        self.user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                         username='tdog', image_url='http://imgur.com/tdog')
        self.user.save()

        # Mock POST data.
        b64_registration_id = 'Zi28NYqEvBdX74vATBujSH8CocmCUj37zqJZ1B5X+Os='
        self.post_data = {
            'registration_id': b64_registration_id,
            'device_id': 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F',
            'name': 'iPhone, 8.2',
            'user': self.user.id,
        }

    def test_create(self):
        url = reverse('apnsdevice-list')
        response = self.client.post(url, self.post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create a new device.
        data = self.post_data
        data['registration_id'] = b2a_hex(a2b_base64(data['registration_id']))
        APNSDevice.objects.get(**data)
