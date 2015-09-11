from __future__ import unicode_literals
from binascii import a2b_base64, b2a_hex
from django.core.urlresolvers import reverse
from django.test import TestCase
from push_notifications.models import APNSDevice, GCMDevice
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

        # Save URLs.
        self.create_url = reverse('apns-list')

    def test_create(self):
        response = self.client.post(self.create_url, self.post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create a APNSDevice.
        APNSDevice.objects.get(**self.post_data)

    def test_create_already_exists(self):
        # Create the APNSDevice.
        data = self.post_data.copy()
        data['user'] = self.user
        device = APNSDevice(**data)
        device.save()

        response = self.client.post(self.create_url, self.post_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class GCMDeviceTests(APITestCase):

    def setUp(self):
        # Mock a user.
        self.user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                         username='tdog', image_url='http://imgur.com/tdog')
        self.user.save()

        # Mock POST data.
        self.post_data = {
            'registration_id': ('APA91bHPRgkF3JUikC4ENAHEeMrd41Zxv3hVZjC9KtT8OvP'
                                'VGJ-hQMRKRrZuJAEcl7B338qju59zJMjw2DELjzEvxwYv7h'
                                'H5Ynpc1ODQ0aT4U4OFEeco8ohsN5PjL1iC2dNtk2BAokeMC'
                                'g2ZXKqpc8FXKmhX94kIxQaa'),
            'device_id': '490154203237518',
            'name': 'Galaxy S6',
            'user': self.user.id,
        }

        # Save URLs.
        self.create_url = reverse('gcm-list')

    def test_create(self):
        response = self.client.post(self.create_url, self.post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create a GCMDevice.
        GCMDevice.objects.get(**self.post_data)

    def test_create_already_exists(self):
        # Create the GCMDevice.
        data = self.post_data.copy()
        data['user'] = self.user
        device = GCMDevice(**data)
        device.save()

        response = self.client.post(self.create_url, self.post_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
