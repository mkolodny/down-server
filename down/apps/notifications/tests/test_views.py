from __future__ import unicode_literals
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
            'registration_id': ('2ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                                '10df230567037dcc4'),
            'device_id': 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F',
            'name': 'iPhone, 8.2',
            'user': self.user.id,
        }

    def test_create(self):
        url = reverse('apnsdevice-list')
        response = self.client.post(url, self.post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create a new device.
        APNSDevice.objects.get(**self.post_data)
