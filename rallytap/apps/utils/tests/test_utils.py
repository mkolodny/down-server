from __future__ import unicode_literals
import json
from django.conf import settings
from django.test import TestCase
import httpretty
import requests
from rest_framework import status
from rallytap.apps.auth.models import User
from ..utils import add_members, remove_member


class MeteorTests(TestCase):

    def setUp(self):
        # Save re-used data.
        self.event_id = 1
        self.user = User(name='Barack Obama', first_name='Barack',
                         last_name='Obama', image_url='http:/facebook.com/img/prez')
        self.user.save()

        # Save URLs.
        self.add_members_url = '{meteor_url}/chats/{chat_id}/members'.format(
                meteor_url=settings.METEOR_URL, chat_id=self.event_id)
        self.remove_member_url = '{meteor_url}/chats/{chat_id}/members/{user_id}'\
                .format(meteor_url=settings.METEOR_URL, chat_id=self.event_id,
                        user_id=self.user.id)

    @httpretty.activate
    def test_add_members(self):
        # Mock the response from the meteor server.
        httpretty.register_uri(httpretty.POST, self.add_members_url)

        add_members(self.event_id, [self.user.id])

        self.assertEqual(httpretty.last_request().body, json.dumps({
            'user_ids': [self.user.id],
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
            add_members(self.event_id, [self.user.id])

    @httpretty.activate
    def test_remove_member(self):
        # Mock the response from the meteor server.
        httpretty.register_uri(httpretty.DELETE, self.remove_member_url)

        remove_member(self.event_id, self.user)

        # It should remove the user to the event's member list on the meteor server.
        self.assertEqual(httpretty.last_request().method, 'DELETE')
        self.assertEqual(httpretty.last_request().body, json.dumps({
            'member': {
                'name': self.user.name,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'image_url': self.user.image_url,
            },
        }))
        auth_header = 'Token {api_key}'.format(api_key=settings.METEOR_KEY)
        self.assertEqual(httpretty.last_request().headers['Authorization'],
                         auth_header)
        self.assertEqual(httpretty.last_request().headers['Content-Type'],
                         'application/json')

    @httpretty.activate
    def test_remove_member_bad_response(self):
        # Mock a bad response from the meteor server.
        httpretty.register_uri(httpretty.DELETE, self.remove_member_url,
                               status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        with self.assertRaises(requests.exceptions.HTTPError):
            remove_member(self.event_id, self.user)
