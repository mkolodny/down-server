from __future__ import unicode_literals
import time
from django.utils import timezone
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APITestCase
from down.apps.auth.models import User
from down.apps.events.models import Event, Invitation, Place
from down.apps.events.serializers import EventSerializer, InvitationSerializer


class EventTests(APITestCase):

    def setUp(self):
        # Mock a user.
        self.user = User(email='aturing@gmail.com', name='Alan Tdog Turing')
        self.user.save()

    def test_create(self):
        url = reverse('event-list')
        data = {
            'title': 'rat fishing!',
            'creator': self.user.id,
            'canceled': False,
            'datetime': int(time.mktime(timezone.now().timetuple())),
            'place': {
                'name': 'Atlantic-Barclays Station',
            },
            'description': 'To the sewers!',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create the place.
        place = data.pop('place')
        Place.objects.get(**place)

        # It should create the event.
        data.pop('datetime') # TODO: Figure out why the saved ms are off.
        event = Event.objects.get(**data)

        # It should return the event.
        serializer = EventSerializer(event)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)

    def test_get(self):
        # Mock a place.
        place = Place(geo='POINT(40.6898319 -73.9904645)')
        place.save()

        # Mock an event.
        event = Event(title='bars?!?!!', creator=self.user,
                      datetime=timezone.now(), place=place,
                      description='bars!!!!')
        event.save()

        url = reverse('event-detail', kwargs={'pk': event.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the event.
        serializer = EventSerializer(event)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)


class InvitationTests(APITestCase):

    def test_create(self):
        # Mock a couple users.
        user1 = User(email='aturing@gmail.com', name='Alan Tdog Turing')
        user1.save()
        user2 = User(email='jclarke@gmail.com', name='Joan Clarke')
        user2.save()

        # Mock a place.
        place = Place(geo='POINT(40.6898319 -73.9904645)')
        place.save()

        # Mock an event
        event = Event(title='bars?!?!!', creator=user1,
                      datetime=timezone.now(), place=place,
                      description='bars!!!!')
        event.save()

        url = reverse('invitation-list')
        data = {
            'to_user': user2.id,
            'event': event.id,
            'accepted': True,
        }
        response = self.client.post(url, data)

        # It should create the invitation.
        invitation = Invitation.objects.get(**data)

        # It should return the invitation.
        serializer = InvitationSerializer(invitation)
        json_invitation = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_invitation)
