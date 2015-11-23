from __future__ import unicode_literals
from datetime import datetime, timedelta
import json
import time
from django.utils import timezone
from django.conf import settings
from django.contrib.gis.geos import Point
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
from rallytap.apps.events.models import Event, Place, RecommendedEvent, SavedEvent
from rallytap.apps.events.serializers import (
    EventSerializer,
    RecommendedEventSerializer,
    SavedEventSerializer,
)
from rallytap.apps.friends.models import Friendship


class EventTests(APITestCase):

    def setUp(self):
        # Mock a user.
        self.user = User()
        self.user.save()

        # Mock the user's friend.
        self.friend1 = User()
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


class RecommendedEventTests(APITestCase):

    def setUp(self):
        # Mock a user.
        self.user = User(location=Point(40.6898319, -73.9904645))
        self.user.save()

        # Authorize the requests with the user's token.
        self.token = Token(user=self.user)
        self.token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # Save urls.
        self.list_url = reverse('recommended-event-list')

    def test_query(self):
        # Mock a recommended event without a location.
        no_location_event = RecommendedEvent(title='drop it like it\'s hot')
        no_location_event.save()

        # Mock a recommended event close by the user.
        place = Place(name='Coopers Craft & Kitchen',
                      geo=Point(40.7270113, -73.9912938))
        place.save()
        nearby_event = RecommendedEvent(title='$1 fish tacos', place=place)
        nearby_event.save()

        # Mock a recommended event far from the user.
        place = Place(name='Bronx Zoo',
                      geo=Point(40.8560079, -73.970945))
        place.save()
        far_event = RecommendedEvent(title='see some giraffes', place=place)
        far_event.save()

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return all non-expired recommended events where the event
        # either doesn't have a location, or the event is within 10 miles of
        # the user.
        recommended_events = [no_location_event, nearby_event]
        serializer = RecommendedEventSerializer(recommended_events, many=True)
        json_recommended_events = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_recommended_events)

    def test_query_not_logged_in(self):
        # Don't include the user's credentials in the request.
        self.client.credentials()

        response = self.client.post(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SavedEventTestCase(APITestCase):

    def setUp(self):
        # Mock a user.
        self.user = User(location=Point(40.6898319, -73.9904645))
        self.user.save()

        # Authorize the requests with the user's token.
        self.token = Token(user=self.user)
        self.token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # Save urls.
        self.list_url = reverse('saved-event-list')

    def test_save_event(self):
        # Mock an event.
        event = Event(title='get jiggy with it', creator=self.user)
        event.save()

        # Mock the user's friend being interested already.
        friend = User(name='Michael Bolton')
        friend.save()
        friend_saved_event = SavedEvent(event=event, user=friend,
                                        location=self.user.location)
        friend_saved_event.save()
        friendship = Friendship(user=self.user, friend=friend)
        friendship.save()

        data = {'event': event.id}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create the saved event.
        saved_event = SavedEvent.objects.get(user=self.user, event=event,
                                             location=self.user.location)

        # It should return the saved event with your friends who have already saved
        # the event nested inside the event.
        context = {'interested': [friend_saved_event]}
        serializer = SavedEventSerializer(saved_event, context=context)
        json_saved_events = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_saved_events)

    def test_save_event_not_logged_in(self):
        # Don't include the user's credentials in the request.
        self.client.credentials()

        response = self.client.post(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
