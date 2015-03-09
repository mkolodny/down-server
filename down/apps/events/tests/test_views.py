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

        # Mock a place.
        self.place = Place(geo='POINT(40.6898319 -73.9904645)')
        self.place.save()

        # Mock an event.
        self.event = Event(title='bars?!?!!', creator=self.user,
                      datetime=timezone.now(), place=self.place,
                      description='bars!!!!')
        self.event.save()


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
        url = reverse('event-detail', kwargs={'pk': self.event.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the event.
        serializer = EventSerializer(self.event)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)

    def test_create_message(self):
        url = reverse('event-messages', kwargs={'pk': self.event.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class InvitationTests(APITestCase):

    def setUp(self):
        # Mock a couple users.
        self.user1 = User(email='aturing@gmail.com', name='Alan Tdog Turing')
        self.user1.save()
        self.user2 = User(email='jclarke@gmail.com', name='Joan Clarke')
        self.user2.save()

        # Mock a place.
        self.place = Place(geo='POINT(40.6898319 -73.9904645)')
        self.place.save()

        # Mock an event
        self.event = Event(title='bars?!?!!', creator=self.user1,
                      datetime=timezone.now(), place=self.place,
                      description='bars!!!!')
        self.event.save()

    def test_create(self):
        url = reverse('invitation-list')
        data = {
            'to_user': self.user2.id,
            'event': self.event.id,
            'accepted': True,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create the invitation.
        invitation = Invitation.objects.get(**data)

        # It should return the invitation.
        serializer = InvitationSerializer(invitation)
        json_invitation = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_invitation)

    def test_update(self):
        # Mock an invitation.
        invitation = Invitation(to_user=self.user2, event=self.event,
                                accepted=False)
        invitation.save()

        url = reverse('invitation-detail', kwargs={'pk': invitation.id})
        data = {
            'to_user': invitation.to_user_id,
            'event': invitation.event.id,
            'accepted': False,
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should update the invitation.
        invitation = Invitation.objects.get(**data)
