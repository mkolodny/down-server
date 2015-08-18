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
        self.post_data = {
            'registration_id': ('8670dc75c6fa765ae1f5d16e34bccdd5fe24b9fa90dd5af8'
                                '1634ea167291a3d7'),
            'device_id': 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F',
            'name': 'iPhone, 8.2',
            'user': self.user.id,
        }

    def test_create(self):
        url = reverse('apnsdevice-list')
        response = self.client.post(url, self.post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        APNSDevice.objects.get(**self.post_data)
