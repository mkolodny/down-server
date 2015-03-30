from __future__ import unicode_literals
import time
from django.utils import timezone
from django.core.urlresolvers import reverse
import mock
from push_notifications.models import APNSDevice
from rest_framework import status
from rest_framework.authtoken.models import Token
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
        registration_id = ('1ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '10df230567037dcc4')
        device_id = 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F'
        self.apns_device = APNSDevice(registration_id=registration_id,
                                      device_id=device_id, name='iPhone, 8.2',
                                      user=self.user)
        self.apns_device.save()

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
                           datetime=timezone.now(), place=self.place,
                           description='bars!!!!')
        self.event.save()
        self.invitation = Invitation(to_user=self.user, event=self.event)
        self.invitation.save()

        # Save urls.
        self.detail_url = reverse('event-detail', kwargs={'pk': self.event.id})

    def test_create(self):
        url = reverse('event-list')
        data = {
            'title': 'rat fishing with the boys over at the place!',
            'creator': self.user.id,
            'canceled': False,
            'datetime': int(time.mktime(timezone.now().timetuple())),
            'place': {
                'name': 'Atlantic-Barclays Station',
            },
            'description': 'To the sewers!',
        }
        response = self.client.post(url, data, format='json')
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

    def test_create_not_logged_in(self):
        # TODO
        pass

    def test_get(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the event.
        serializer = EventSerializer(self.event)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)

    def test_get_not_invited(self):
        # We know a user was invited because an invitation exists with them as
        # the `to_user`. So, to mock the user not being invited, delete their
        # invitation.
        self.invitation.delete()

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_create_message(self, mock_send):
        # Mock two of the user's friends.
        friend = User(name='Michael Jordan', email='mj@gmail.com',
                      image_url='http://imgur.com/mj')
        friend.save()
        registration_id = ('2ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '10df230567037dcc4')
        device_id = 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F'
        apns_device1 = APNSDevice(registration_id=registration_id,
                                  device_id=device_id, name='iPhone, 8.2',
                                  user=friend)
        apns_device1.save()

        friend1 = User(name='Bruce Lee', email='blee@gmail.com',
                       image_url='http://imgur.com/blee')
        friend1.save()
        registration_id = ('3ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '10df230567037dcc4')
        device_id = 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F'
        apns_device2 = APNSDevice(registration_id=registration_id,
                                  device_id=device_id, name='iPhone, 8.2',
                                  user=friend1)
        apns_device2.save()

        # Mock the friends being down for the event.
        invitation = Invitation(to_user=friend, event=self.event, accepted=True)
        invitation.save()
        invitation = Invitation(to_user=friend1, event=self.event, accepted=True)
        invitation.save()

        # Clear any previous notifications
        mock_send.reset_mock()

        url = reverse('event-messages', kwargs={'pk': self.event.id})
        data = {
            'text': 'So down!',
            'user': friend1.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should notify the user and the first friend that their friend
        # commented on the event.
        tokens = [
            self.apns_device.registration_id,
            apns_device1.registration_id,
        ]
        if len(self.event.title) > 25:
            activity = self.event.title[:25] + '...'
        else:
            activity = self.event.title
        message = '{name} to {activity}: {text}'.format(
                name=friend1.name, activity=activity, text=data['text'])
        mock_send.assert_called_once_with(registration_ids=tokens, alert=message)


class InvitationTests(APITestCase):

    def setUp(self):
        # Mock a couple users.
        self.user1 = User(email='aturing@gmail.com', name='Alan Tdog Turing')
        self.user1.save()
        self.user2 = User(email='jclarke@gmail.com', name='Joan Clarke')
        self.user2.save()

        # Mock the user-to-be-invited's device
        registration_id = ('2ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '10df230567037dcc4')
        device_id = 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F'
        self.apns_device = APNSDevice(registration_id=registration_id,
                                      device_id=device_id,
                                      name='iPhone, 8.2',
                                      user=self.user2)
        self.apns_device.save()

        # Mock a place.
        self.place = Place(name='Founder House',
                           geo='POINT(40.6898319 -73.9904645)')
        self.place.save()

        # Mock an event
        self.event = Event(title='bars?!?!!', creator=self.user1,
                      datetime=timezone.now(), place=self.place,
                      description='bars!!!!')
        self.event.save()

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_create(self, mock_send):
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

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_update(self, mock_send):
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
