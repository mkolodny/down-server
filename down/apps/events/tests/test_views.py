from __future__ import unicode_literals
import json
import time
from django.utils import timezone
from django.conf import settings
from django.core.urlresolvers import reverse
import httpretty
import mock
from push_notifications.models import APNSDevice
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APITestCase
from twilio import TwilioRestException
from down.apps.auth.models import User, UserPhone
from down.apps.events.models import Event, Invitation, Place
from down.apps.events.serializers import EventSerializer, InvitationSerializer


class EventTests(APITestCase):

    # We have to mock the function that sends push notifications, since 
    # inviting people to events will send push notifications.
    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def setUp(self, mock_send):
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
                           datetime=timezone.now(), place=self.place)
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
                'geo': 'POINT(40.685339 -73.979361)',
            },
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

    def test_update(self):
        data = {
            'title': self.event.title,
            'creator': self.event.creator_id,
            'canceled': self.event.canceled,
            'datetime': int(time.mktime(self.event.datetime.timetuple())),
            'place': {
                'name': '540 State St',
                'geo': 'POINT(40.685339 -73.979361)',
            },
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should create the place.
        place_data = data.pop('place')
        place = Place.objects.get(**place_data)

        # It should update the event.
        event = Event.objects.get(id=self.event.id)
        self.assertEqual(event.place_id, place.id)

        # It should return the event.
        serializer = EventSerializer(event)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)

    def test_update_not_creator(self):
        # Mock another user.
        user = User(name='Michael Jordan', email='mj@gmail.com',
                    username='mj', image_url='http://imgur.com/mj')
        user.save()

        # Invite them to the event.
        invitation = Invitation(from_user=self.user, to_user=user, event=self.event)
        invitation.save()

        # Log them in.
        token = Token(user=user)
        token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token '+token.key)

        response = self.client.put(self.detail_url, None, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_create_message(self, mock_send):
        # Mock two of the user's friends.
        friend1 = User(name='Michael Jordan', email='mj@gmail.com',
                       username='mj', image_url='http://imgur.com/mj')
        friend1.save()
        registration_id = ('2ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '10df230567037dcc4')
        device_id = 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F'
        friend1_device = APNSDevice(registration_id=registration_id,
                                  device_id=device_id, name='iPhone, 8.2',
                                  user=friend1)
        friend1_device.save()

        friend2 = User(name='Bruce Lee', email='blee@gmail.com',
                       username='blee', image_url='http://imgur.com/blee')
        friend2.save()
        registration_id = ('3ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '10df230567037dcc4')
        device_id = 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F'
        friend2_device = APNSDevice(registration_id=registration_id,
                                    device_id=device_id, name='iPhone, 8.2',
                                    user=friend2)
        friend2_device.save()

        # Mock one friend being down, and another friend not having responded yet.
        invitation = Invitation(from_user=self.user, to_user=friend1,
                                event=self.event, response=Invitation.ACCEPTED)
        invitation.save()
        invitation = Invitation(from_user=self.user, to_user=friend2,
                                event=self.event, response=Invitation.NO_RESPONSE)
        invitation.save()

        # Clear any previous notifications
        mock_send.reset_mock()

        data = {'text': 'So down!'}
        response = self.client.post(self.create_message_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should notify the user and the first friend that their friend
        # commented on the event.
        tokens = [
            friend1_device.registration_id,
            friend2_device.registration_id,
        ]
        if len(self.event.title) > 25:
            activity = self.event.title[:25] + '...'
        else:
            activity = self.event.title
        message = '{name} to {activity}: {text}'.format(
                name=self.user.name, activity=activity, text=data['text'])
        mock_send.assert_any_call(registration_ids=tokens, alert=message)

    def test_create_message_not_invited(self):
        # Uninvite the logged in user.
        self.invitation.delete()
        
        data = {'text': 'So down!'}
        response = self.client.post(self.create_message_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class InvitationTests(APITestCase):

    # We have to mock the function that sends push notifications, since 
    # inviting people to events will send push notifications.
    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def setUp(self, mock_send):
        self.patcher = mock.patch('requests.patch')
        self.mock_patch = self.patcher.start()

        # Mock a couple users.
        self.user1 = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                          username='tdog')
        self.user1.save()
        self.user2 = User(email='jclarke@gmail.com', name='Joan Clarke',
                          username='jcke')
        self.user2.save()
        self.user3 = User(name='Bruce Lee') # SMS users don't have a username.
        self.user3.save()

        # Authorize the requests with the user's token.
        self.token = Token(user=self.user1)
        self.token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # Mock the users with usernames' devices.
        registration_id = ('1ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '10df230567037dcc4')
        device_id = 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F'
        self.user1_device = APNSDevice(registration_id=registration_id,
                                       device_id=device_id, name='iPhone, 8.2',
                                       user=self.user1)
        self.user1_device.save()

        registration_id = ('2ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '10df230567037dcc4')
        device_id = 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F'
        self.user2_device = APNSDevice(registration_id=registration_id,
                                       device_id=device_id, name='iPhone, 8.2',
                                       user=self.user2)
        self.user2_device.save()

        # Mock the user without a username's user phone.
        self.user3_phone = UserPhone(user=self.user3, phone='+12036227310')
        self.user3_phone.save()

        # Mock a place.
        self.place = Place(name='Founder House',
                           geo='POINT(40.6898319 -73.9904645)')
        self.place.save()

        # Mock an event
        self.event = Event(title='bars?!?!!', creator=self.user1,
                           datetime=timezone.now(), place=self.place)
        self.event.save()

        # Save urls.
        self.list_url = reverse('invitation-list')

        # Save POST data.
        self.post_data = {
            'invitations': [
                {
                    'from_user': self.user1.id,
                    'to_user': self.user1.id,
                    'event': self.event.id,
                    'response': Invitation.ACCEPTED,
                },
                {
                    'from_user': self.user1.id,
                    'to_user': self.user2.id,
                    'event': self.event.id,
                    'response': Invitation.NO_RESPONSE,
                },
                {
                    'from_user': self.user1.id,
                    'to_user': self.user3.id,
                    'event': self.event.id,
                    'response': Invitation.NO_RESPONSE,
                },
            ],
        }

    def tearDown(self):
        self.patcher.stop()

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    @mock.patch('down.apps.events.models.TwilioRestClient')
    @mock.patch('down.apps.events.models.get_invite_sms')
    @mock.patch('down.apps.events.models.requests')
    def test_bulk_create(self, mock_requests, mock_get_message, mock_twilio,
                         mock_apns):
        # Mock the getting the invitation message.
        mock_message = 'Barack Obama invited you to ball hard'
        mock_get_message.return_value = mock_message

        # Mock the Twilio SMS API.
        mock_client = mock.MagicMock()
        mock_twilio.return_value = mock_client

        response = self.client.post(self.list_url, self.post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create the invitations.
        invitations = Invitation.objects.filter(from_user=self.user1,
                                                event=self.event)
        self.assertEqual(invitations.count(),
                         len(self.post_data['invitations']))

        # It should send push notifications to users with devices.
        token = self.user2_device.registration_id
        message = '{name} invited you to {activity}'.format(
                name=self.user1.name,
                activity=self.event.title)
        mock_apns.assert_any_call(registration_ids=[token], alert=message,
                                  badge=1)

        # It should use the mock to get the SMS invite message.
        mock_get_message.assert_called_with(self.user1, self.event)

        # It should init the Twilio client with the proper params.
        mock_twilio.assert_called_with(settings.TWILIO_ACCOUNT,
                                       settings.TWILIO_TOKEN)

        # It should send SMS to users without devices.
        phone = unicode(self.user3_phone.phone)
        mock_client.messages.create.assert_called_with(to=phone, 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=mock_message)

        # It should add the users to the firebase members list.
        url = ('{firebase_url}/events/members/{event_id}/.json'
               '?auth={firebase_secret}').format(
                firebase_url=settings.FIREBASE_URL,
                event_id=self.event.id,
                firebase_secret=settings.FIREBASE_SECRET)
        json_invitations = json.dumps({
            invite['to_user']: True
            for invite in self.post_data['invitations']
        })
        mock_requests.patch.assert_called_with(url, json_invitations)

        # It should return the invitations.
        serializer = InvitationSerializer(invitations, many=True)
        json_invitations = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_invitations)

    def test_bulk_create_not_logged_in(self):
        # Don't include the user's credentials in the request.
        self.client.credentials()

        response = self.client.post(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_bulk_create_not_logged_in_user(self):
        # Log the second user in.
        token = Token(user=self.user2)
        token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token '+token.key)

        # Invite the second user.
        invitation = Invitation(from_user=self.user1, to_user=self.user2,
                                event=self.event)
        invitation.save()

        response = self.client.post(self.list_url, self.post_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    @mock.patch('down.apps.events.models.TwilioRestClient')
    @mock.patch('down.apps.events.models.get_invite_sms')
    def test_bulk_create_as_creator_not_invited(self, mock_sms, mock_twilio,
                                                mock_send):
        # Mock the sms message.
        mock_sms.return_value = '<user> invited you to <event>'

        # Mock the Twilio SMS API.
        mock_client = mock.MagicMock()
        mock_twilio.return_value = mock_client

        response = self.client.post(self.list_url, self.post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create the invitations.
        invitations = Invitation.objects.filter(from_user=self.user1,
                                                event=self.event)
        self.assertEqual(invitations.count(),
                         len(self.post_data['invitations']))

        # It should return the invitations.
        serializer = InvitationSerializer(invitations, many=True)
        json_invitations = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_invitations)

    def test_bulk_create_not_invited(self):
        # Log the second user in.
        token = Token(user=self.user2)
        token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token '+token.key)

        data = {
            'invitations': [
                {
                    'from_user': self.user2.id,
                    'to_user': self.user3.id,
                    'event': self.event.id,
                },
            ],
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_bulk_create_event_doesnt_exist(self):
        # Make sure the event doesn't exist.
        event_id = 0
        with self.assertRaises(Event.DoesNotExist):
            Event.objects.get(id=event_id)

        data = {
            'invitations': [
                {
                    'from_user': self.user1.id,
                    'to_user': self.user1.id,
                    'event': event_id,
                }, 
            ],
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_create_mixed_events(self):
        # Append an invitation with a different event id.
        self.post_data['invitations'].append({
            'from_user': self.user1.id,
            'to_user': self.user1.id,
            'event': 0,
        })
        response = self.client.post(self.list_url, self.post_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_create_mixed_from_user(self):
        # Give the last invitation a different from_user id.
        self.post_data['invitations'][-1] = {
            'from_user': self.user2.id,
            'to_user': self.user3.id,
            'event': self.event.id,
        }
        response = self.client.post(self.list_url, self.post_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_create_others_down(self):
        # Set another user's response other than the user who sent the
        # invitations to "down".
        self.post_data['invitations'][1]['response'] = Invitation.ACCEPTED

        response = self.client.post(self.list_url, self.post_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_update(self, mock_send):
        # Mock an invitation.
        invitation = Invitation(from_user=self.user1, to_user=self.user2,
                                event=self.event, response=Invitation.DECLINED)
        invitation.save()

        # Save the most recent time the event was updated.
        updated_at = self.event.updated_at

        url = reverse('invitation-detail', kwargs={'pk': invitation.id})
        data = {
            'from_user': invitation.from_user_id,
            'to_user': invitation.to_user_id,
            'event': invitation.event_id,
            'response': Invitation.DECLINED,
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should update the invitation.
        invitation = Invitation.objects.get(**data)

        # It should update the event.
        event = Event.objects.get(id=invitation.event_id)
        self.assertGreater(event.updated_at, updated_at)
