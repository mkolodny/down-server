from __future__ import unicode_literals
from datetime import datetime, timedelta
import json
import time
from django.utils import timezone
from django.conf import settings
from django.core.urlresolvers import reverse
from hashids import Hashids
import httpretty
import mock
import pytz
import requests
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APITestCase
from twilio import TwilioRestException
from rallytap.apps.auth.models import Points, User, UserPhone
from rallytap.apps.events.models import Event, Place
from rallytap.apps.events.serializers import EventSerializer
from rallytap.apps.friends.models import Friendship


class EventTests(APITestCase):

    def setUp(self):
        # Mock a user.
        self.user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                         username='tdog')
        self.user.save()

        # Mock two of the user's friend1s
        self.friend1 = User(email='jclarke@gmail.com', name='Joan Clarke',
                           username='jcke')
        self.friend1.save()

        # Authorize the requests with the user's token.
        self.token = Token(user=self.user)
        self.token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # Mock a place.
        self.place = Place(name='Founder House',
                           geo='POINT(40.6898319 -73.9904645)')
        self.place.save()

        # Mock an event.
        self.event = Event(title='bars?!?!!', creator=self.user,
                           datetime=timezone.now(), place=self.place)
        self.event.save()

        # Save post data.
        self.post_data = {
            'title': 'rat fishing with the boys!',
            'datetime': timezone.now().strftime(settings.DATETIME_FORMAT),
            'place': {
                'name': 'Atlantic-Barclays Station',
                'geo': 'POINT(40.685339 -73.979361)',
            },
        }

        # Save urls.
        self.list_url = reverse('event-list')
        self.detail_url = reverse('event-detail', kwargs={'pk': self.event.id})

    def test_create(self):
        data = self.post_data
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create the place.
        place = data.pop('place')
        Place.objects.get(**place)

        # It should create the event.
        data.pop('datetime') # TODO: Figure out why the saved ms are off.
        event = Event.objects.get(**data)

        # It should send notifications to the users who were invited aside from
        # the creator.
        """
        user_ids = [self.friend1.id]
        message = '{name}: Are you down to {activity}?'.format(name=self.user.name,
                                                               activity=event.title)
        mock_send_message.assert_called_once_with(user_ids, message,
                                                  event_id=event.id,
                                                  from_user=self.user)
        """

        # It should return the event.
        serializer = EventSerializer(event)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)

    def test_create_not_logged_in(self):
        # Don't include the user's credentials in the request.
        self.client.credentials()

        response = self.client.post(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    """
    @mock.patch('rallytap.apps.events.serializers.add_members')
    def test_create_add_members_error(self, mock_add_members):
        mock_add_members.side_effect = requests.exceptions.HTTPError()

        response = self.client.post(self.list_url, self.post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
    """

    def test_get(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the event.
        event = Event.objects.get(id=self.event.id)
        serializer = EventSerializer(event)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)
