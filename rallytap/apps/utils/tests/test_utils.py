from __future__ import unicode_literals
import json
from django.conf import settings
from django.test import TestCase
import httpretty
import requests
from rest_framework import status
from rallytap.apps.auth.models import User
from ..utils import add_members


class MeteorTests(TestCase):

    def setUp(self):
        # Save re-used data.
        self.event_id = 1
        self.user = User(name='Barack Obama', first_name='Barack',
                         last_name='Obama', image_url='http:/facebook.com/img/prez')
        self.user.save()

        # Save URLs.
        self.add_members_url = '{meteor_url}/events/{event_id}/members'.format(
                meteor_url=settings.METEOR_URL, event_id=self.event_id)

    @httpretty.activate
    def test_add_members(self):
        # Mock the response from the meteor server.
        httpretty.register_uri(httpretty.POST, self.add_members_url)

        add_members(self.event_id, self.user.id)

        self.assertEqual(httpretty.last_request().body, json.dumps({
            'user_id': self.user.id,
        }))
        auth_header = 'Token {api_key}'.format(api_key=settings.METEOR_KEY)
        self.assertEqual(httpretty.last_request().headers['Authorization'],
                         auth_header)
        self.assertEqual(httpretty.last_request().headers['Content-Type'],
                         'application/json')

    @httpretty.activate
    def test_add_members_bad_response(self):
        # Mock a bad response from the meteor server.
        httpretty.register_uri(httpretty.POST, self.add_members_url,
                               status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        with self.assertRaises(requests.exceptions.HTTPError):
            add_members(self.event_id, self.user.id)
