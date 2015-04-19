from __future__ import unicode_literals
import time
from django.utils import timezone
from django.conf import settings
from django.core.urlresolvers import reverse
import mock
from push_notifications.models import APNSDevice
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APITestCase
from twilio import TwilioRestException
from down.apps.auth.models import User
from down.apps.events.models import Event, Invitation, Place
from down.apps.events.serializers import EventSerializer, InvitationSerializer


class EventTests(APITestCase):

    def setUp(self):
        self.patcher = mock.patch('requests.patch')
        self.mock_patch = self.patcher.start()

        # Mock a user.
        self.user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                         username='tdog')
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
        self.invitation = Invitation(from_user=self.user, to_user=self.user,
                                     event=self.event)
        self.invitation.save()

        # Save urls.
        self.list_url = reverse('event-list')
        self.detail_url = reverse('event-detail', kwargs={'pk': self.event.id})
        self.create_message_url = reverse('event-messages', kwargs={
            'pk': self.event.id,
        })
    
    def tearDown(self):
        self.patcher.stop()

    def test_create(self):
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
        response = self.client.post(self.list_url, data, format='json')
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
        # Don't include the user's credentials in the request.
        self.client.credentials()

        response = self.client.post(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

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
                      username='mj', image_url='http://imgur.com/mj')
        friend.save()
        registration_id = ('2ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '10df230567037dcc4')
        device_id = 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F'
        apns_device1 = APNSDevice(registration_id=registration_id,
                                  device_id=device_id, name='iPhone, 8.2',
                                  user=friend)
        apns_device1.save()

        friend1 = User(name='Bruce Lee', email='blee@gmail.com',
                       username='blee', image_url='http://imgur.com/blee')
        friend1.save()
        registration_id = ('3ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '10df230567037dcc4')
        device_id = 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F'
        apns_device2 = APNSDevice(registration_id=registration_id,
                                  device_id=device_id, name='iPhone, 8.2',
                                  user=friend1)
        apns_device2.save()

        # Mock the friends being down for the event.
        invitation = Invitation(from_user=self.user, to_user=friend,
                                event=self.event, accepted=True)
        invitation.save()
        invitation = Invitation(from_user=self.user, to_user=friend1,
                                event=self.event, accepted=True)
        invitation.save()

        # Clear any previous notifications
        mock_send.reset_mock()

        # Set the user's friend to be the logged in user.
        token = Token(user=friend1)
        token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        data = {'text': 'So down!'}
        response = self.client.post(self.create_message_url, data)
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

    def test_create_message_not_invited(self):
        # Uninvite the logged in user.
        self.invitation.delete()
        
        data = {'text': 'So down!'}
        response = self.client.post(self.create_message_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class InvitationTests(APITestCase):

    def setUp(self):
        self.patcher = mock.patch('requests.patch')
        self.mock_patch = self.patcher.start()

        # Mock a couple users.
        self.user1 = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                          username='tdog')
        self.user1.save()
        self.user2 = User(email='jclarke@gmail.com', name='Joan Clarke',
                          username='jcke')
        self.user2.save()

        # Authorize the requests with the user's token.
        self.token = Token(user=self.user1)
        self.token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

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
        self.invitation = Invitation(event=self.event, from_user=self.user1,
                                     to_user=self.user1)
        self.invitation.save()

        # Save urls.
        self.list_url = reverse('invitation-list')

    def tearDown(self):
        self.patcher.stop()

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_create(self, mock_send):
        data = {
            'from_user': self.user1.id,
            'to_user': self.user2.id,
            'event': self.event.id,
            'accepted': True,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create the invitation.
        invitation = Invitation.objects.get(**data)

        # It should return the invitation.
        serializer = InvitationSerializer(invitation)
        json_invitation = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_invitation)

    def test_create_not_logged_in(self):
        # Don't include the user's credentials in the request.
        self.client.credentials()

        response = self.client.post(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_not_logged_in_user(self):
        # Log the second user in.
        token = Token(user=self.user2)
        token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token '+token.key)

        # Invite the second user.
        invitation = Invitation(from_user=self.user1, to_user=self.user2,
                                event=self.event)
        invitation.save()

        data = {
            'from_user': self.user1.id,
            'to_user': self.user2.id,
            'event': self.event.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_create_as_creator_not_invited(self, mock_send):
        # Delete the logged in user's invitation.
        self.invitation.delete()

        data = {
            'from_user': self.user1.id,
            'to_user': self.user2.id,
            'event': self.event.id,
            'accepted': True,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create the invitation.
        invitation = Invitation.objects.get(**data)

        # It should return the invitation.
        serializer = InvitationSerializer(invitation)
        json_invitation = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_invitation)

    def test_create_not_invited(self):
        # Log the second user in.
        token = Token(user=self.user2)
        token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token '+token.key)

        # Mock a third user.
        user = User(name='Marie Curie', email='mcurie@gmail.com',
                    username='mcurie')
        user.save()

        data = {
            'from_user': self.user2.id,
            'to_user': user.id,
            'event': self.event.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_event_doesnt_exist(self):
        # Make sure the event doesn't exist.
        event_id = 0
        with self.assertRaises(Event.DoesNotExist):
            Event.objects.get(id=event_id)

        data = {
            'from_user': self.user1.id,
            'to_user': self.user1.id,
            'event': event_id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_update(self, mock_send):
        # Mock an invitation.
        invitation = Invitation(from_user=self.user1, to_user=self.user2,
                                event=self.event, accepted=False)
        invitation.save()

        url = reverse('invitation-detail', kwargs={'pk': invitation.id})
        data = {
            'from_user': invitation.from_user_id,
            'to_user': invitation.to_user_id,
            'event': invitation.event.id,
            'accepted': False,
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should update the invitation.
        invitation = Invitation.objects.get(**data)
