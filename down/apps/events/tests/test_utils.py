from __future__ import unicode_literals
import json
from django.conf import settings
from django.test import TestCase
import httpretty
import requests
from rest_framework import status
from ..utils import add_member, remove_member


class MeteorTests(TestCase):

    def setUp(self):
        # Save re-used data.
        self.event_id = 1
        self.user_id = 2

        # Save URLs.
        self.add_member_url = '{meteor_url}/events/{event_id}/members'.format(
                meteor_url=settings.METEOR_URL, event_id=self.event_id)
        self.remove_member_url = '{meteor_url}/events/{event_id}/members/{user_id}' \
                .format(meteor_url=settings.METEOR_URL, event_id=self.event_id,
                        user_id=self.user_id)

    @httpretty.activate
    def test_add_member(self):
        # Mock the response from the meteor server.
        httpretty.register_uri(httpretty.POST, self.add_member_url)

        add_member(self.event_id, self.user_id)

        # It should add the user to the event's member list on the meteor server.
        # TODO: Get token auth going.
        # http://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication
        self.assertEqual(httpretty.last_request().body, json.dumps({
            #'api_key': settings.METEOR_KEY,
            'user_id': self.user_id,
        }))
        auth_header = 'Token {api_key}'.format(api_key=settings.METEOR_KEY)
        self.assertEqual(httpretty.last_request().headers['Authorization'],
                         auth_header)

    @httpretty.activate
    def test_add_member_bad_response(self):
        # Mock a bad response from the meteor server.
        httpretty.register_uri(httpretty.POST, self.add_member_url,
                               status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        with self.assertRaises(requests.exceptions.HTTPError):
            add_member(self.event_id, self.user_id)

    @httpretty.activate
    def test_remove_member(self):
        # Mock the response from the meteor server.
        httpretty.register_uri(httpretty.DELETE, self.remove_member_url)

        remove_member(self.event_id, self.user_id)

        # It should remove the user to the event's member list on the meteor server.
        self.assertEqual(httpretty.last_request().method, 'DELETE')
        auth_header = 'Token {api_key}'.format(api_key=settings.METEOR_KEY)
        self.assertEqual(httpretty.last_request().headers['Authorization'],
                         auth_header)

    @httpretty.activate
    def test_remove_member_bad_response(self):
        # Mock a bad response from the meteor server.
        httpretty.register_uri(httpretty.DELETE, self.remove_member_url,
                               status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        with self.assertRaises(requests.exceptions.HTTPError):
            remove_member(self.event_id, self.user_id)
