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
from push_notifications.models import APNSDevice
import pytz
import requests
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APITestCase
from twilio import TwilioRestException
from down.apps.auth.models import User, UserPhone
from down.apps.events.models import (
    Event,
    Invitation,
    LinkInvitation,
    Place,
    get_event_date,
)
from down.apps.events.serializers import (
    EventSerializer,
    InvitationSerializer,
    EventInvitationSerializer,
    LinkInvitationSerializer,
)


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

        # Mock two of the user's friend1s
        self.friend1 = User(email='jclarke@gmail.com', name='Joan Clarke',
                           username='jcke')
        self.friend1.save()
        registration_id = ('2ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '10df230567037dcc4')
        device_id = 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F'
        self.friend1_device = APNSDevice(registration_id=registration_id,
                                         device_id=device_id, name='iPhone, 8.2',
                                         user=self.friend1)
        self.friend1_device.save()

        # This user doesn't have the app yet, so they only have a name.
        self.friend2 = User(name='Richard Feynman')
        self.friend2.save()
        self.friend2_phone = UserPhone(phone='+19178699626', user=self.friend2)
        self.friend2_phone.save()

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
        self.user_invitation = Invitation(from_user=self.user, to_user=self.user,
                                          event=self.event,
                                          response=Invitation.ACCEPTED)
        self.user_invitation.save()
        self.friend1_invitation = Invitation(from_user=self.user,
                                             to_user=self.friend1,
                                             event=self.event,
                                             response=Invitation.MAYBE)
        self.friend1_invitation.save()
        self.friend2_invitation = Invitation(from_user=self.user,
                                             to_user=self.friend2,
                                             event=self.event)
        self.friend2_invitation.save()

        # Save SMS details.
        self.signature = '\n--\nSent from Down (http://down.life/app)'

        # Save post data.
        self.user_invitation_data = {
            'to_user': self.user.id,
        }
        self.friend_invitation_data = {
            'to_user': self.friend1.id,
        }
        self.post_data = {
            'title': 'rat fishing with the boys!',
            'datetime': timezone.now().strftime(settings.DATETIME_FORMAT),
            'comment': 'they\'re everywhere!!!',
            'place': {
                'name': 'Atlantic-Barclays Station',
                'geo': 'POINT(40.685339 -73.979361)',
            },
            'invitations': [
                self.user_invitation_data,
                self.friend_invitation_data,
            ],
        }

        # Save urls.
        self.list_url = reverse('event-list')
        self.detail_url = reverse('event-detail', kwargs={'pk': self.event.id})
        self.create_message_url = reverse('event-messages', kwargs={
            'pk': self.event.id,
        })
        self.invitations_url = reverse('event-invitations', kwargs={
            'pk': self.event.id
        })
    
    def tearDown(self):
        self.patcher.stop()

    @mock.patch('down.apps.events.serializers.add_member')
    @mock.patch('down.apps.events.models.Invitation.objects.bulk_create')
    def test_create(self, mock_bulk_create, mock_add_member):
        data = self.post_data
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create the place.
        place = data.pop('place')
        Place.objects.get(**place)

        # It should create the event.
        data.pop('datetime') # TODO: Figure out why the saved ms are off.
        data.pop('invitations') # The event model doesn't have invitations.
        event = Event.objects.get(**data)

        # It should bulk create two invitations.
        self.assertTrue(mock_bulk_create.called)
        call_args = mock_bulk_create.call_args[0][0]
        user_invitation_call = call_args[0]
        self.assertEqual(user_invitation_call.event_id, event.id)
        self.assertEqual(user_invitation_call.response, Invitation.MAYBE)
        self.assertEqual(user_invitation_call.to_user_id, self.user.id)
        self.assertEqual(user_invitation_call.from_user_id, self.user.id)
        friend_invitation_call = call_args[1]
        self.assertEqual(friend_invitation_call.event_id, event.id)
        self.assertEqual(friend_invitation_call.response, Invitation.NO_RESPONSE)
        self.assertEqual(friend_invitation_call.to_user_id, self.friend1.id)
        self.assertEqual(friend_invitation_call.from_user_id, self.user.id)

        # It should add the creator to the members list.
        mock_add_member.assert_called_once_with(event.id, event.creator_id)

        # It should return the event.
        serializer = EventSerializer(event)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)

    def test_create_not_logged_in(self):
        # Don't include the user's credentials in the request.
        self.client.credentials()

        response = self.client.post(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @mock.patch('down.apps.events.serializers.add_member')
    def test_create_add_member_error(self, mock_add_member):
        mock_add_member.side_effect = requests.exceptions.HTTPError()

        response = self.client.post(self.list_url, self.post_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_get(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the event.
        event = Event.objects.get(id=self.event.id)
        serializer = EventSerializer(event)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)

    def test_get_not_invited(self):
        # We know a user was invited because an invitation exists with them as
        # the `to_user`. So, to mock the user not being invited, delete their
        # invitation.
        self.user_invitation.delete()

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    @mock.patch('down.apps.events.serializers.TwilioRestClient')
    @mock.patch('down.apps.events.serializers.get_event_date')
    def test_update_place_and_datetime(self, mock_date, mock_twilio, mock_apns):
        # TODO: Figure out why this test is taking so long.
        # Mock the localized date string.
        date = 'Thursday, Jun. 4 @ 6 PM'
        mock_date.return_value = date

        # Mock the Twilio SMS API.
        mock_client = mock.MagicMock()
        mock_twilio.return_value = mock_client

        data = {
            'title': self.event.title,
            'creator': self.event.creator_id,
            'canceled': self.event.canceled,
            'datetime': timezone.now().strftime(settings.DATETIME_FORMAT),
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
        self.assertGreater(event.datetime, self.event.datetime)

        # It should notify the users who haven't declined their invitation about
        # the changes.

        # It should send push notifications to users with devices.
        registration_ids = [self.friend1_device.registration_id]
        notif = ('{name} changed the location and time where {activity} is'
                 ' happening.') \
                .format(name=event.creator.name, activity=event.title)
        mock_apns.assert_any_call(registration_ids=registration_ids, alert=notif,
                                  badge=1)

        # It should init the Twilio client with the proper params.
        mock_twilio.assert_called_with(settings.TWILIO_ACCOUNT,
                                       settings.TWILIO_TOKEN)

        # It should send SMS to users without devices.
        phone = unicode(self.friend2_phone.phone)
        sms_extra = (' The new location is {place}, and the new time is'
                     ' {date}.').format(place=place.name, date=date)
        sms = notif + sms_extra + self.signature
        mock_client.messages.create.assert_called_with(to=phone, 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=sms)

        # It should return the event.
        serializer = EventSerializer(event)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    @mock.patch('down.apps.events.serializers.TwilioRestClient')
    def test_update_place(self, mock_twilio, mock_apns):
        # Mock the Twilio SMS API.
        mock_client = mock.MagicMock()
        mock_twilio.return_value = mock_client

        data = {
            'title': self.event.title,
            'creator': self.event.creator_id,
            'canceled': self.event.canceled,
            'datetime': self.event.datetime.strftime(settings.DATETIME_FORMAT),
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

        # It should notify the users who haven't declined their invitation about
        # the changes.

        # It should send push notifications to users with devices.
        registration_ids = [self.friend1_device.registration_id]
        notif = ('{name} changed the location where {activity} is'
                 ' happening.').format(name=event.creator.name,
                                       activity=event.title)
        mock_apns.assert_any_call(registration_ids=registration_ids, alert=notif,
                                  badge=1)

        # It should init the Twilio client with the proper params.
        mock_twilio.assert_called_with(settings.TWILIO_ACCOUNT,
                                       settings.TWILIO_TOKEN)

        # It should send SMS to users without devices.
        phone = unicode(self.friend2_phone.phone)
        sms_extra = ' The new location is {place}.'.format(place=place.name)
        sms = notif + sms_extra + self.signature
        mock_client.messages.create.assert_called_with(to=phone, 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=sms)

        # It should return the event.
        serializer = EventSerializer(event)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    @mock.patch('down.apps.events.serializers.TwilioRestClient')
    @mock.patch('down.apps.events.serializers.get_event_date')
    def test_update_datetime(self, mock_date, mock_twilio, mock_apns):
        # Mock the localized date string.
        date = 'Thursday, Jun. 4 @ 6 PM'
        mock_date.return_value = date

        # Mock the Twilio SMS API.
        mock_client = mock.MagicMock()
        mock_twilio.return_value = mock_client

        dt = timezone.now()
        coords = self.place.geo.coords
        data = {
            'title': self.event.title,
            'creator': self.event.creator_id,
            'canceled': self.event.canceled,
            'datetime': dt.strftime(settings.DATE_FORMAT),
            'place': {
                'name': self.place.name,
                'geo': 'POINT({lat} {lng})'.format(lat=coords[0], lng=coords[1]),
            },
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should update the event.
        event = Event.objects.get(id=self.event.id)
        self.assertEqual(event.datetime, dt)

        # It should notify the users who haven't declined their invitation about
        # the changes.

        # It should send push notifications to users with devices.
        registration_ids = [self.friend1_device.registration_id]
        notif = ('{name} changed the time when {activity} is'
                 ' happening.').format(name=event.creator.name,
                                       activity=event.title)
        mock_apns.assert_any_call(registration_ids=registration_ids, alert=notif,
                                  badge=1)

        # It should init the Twilio client with the proper params.
        mock_twilio.assert_called_with(settings.TWILIO_ACCOUNT,
                                       settings.TWILIO_TOKEN)

        # It should send SMS to users without devices.
        phone = unicode(self.friend2_phone.phone)
        sms_extra = ' The new time is {date}.'.format(date=date)
        sms = notif + sms_extra + self.signature
        mock_client.messages.create.assert_called_with(to=phone, 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=sms)

        # It should return the event.
        serializer = EventSerializer(event)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    @mock.patch('down.apps.events.serializers.TwilioRestClient')
    @mock.patch('down.apps.events.serializers.get_event_date')
    def test_update_datetime_remove_place(self, mock_date, mock_twilio, mock_apns):
        # Mock the localized date string.
        date = 'Thursday, Jun. 4 @ 6 PM'
        mock_date.return_value = date

        # Mock the Twilio SMS API.
        mock_client = mock.MagicMock()
        mock_twilio.return_value = mock_client

        coords = self.place.geo.coords
        dt = timezone.now()
        data = {
            'title': self.event.title,
            'creator': self.event.creator_id,
            'canceled': self.event.canceled,
            'datetime': dt.strftime(settings.DATETIME_FORMAT),
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should update the event.
        event = Event.objects.get(id=self.event.id)
        self.assertEqual(event.datetime, dt)
        self.assertIsNone(event.place)

        # It should notify the users who haven't declined their invitation about
        # the changes.

        # It should send push notifications to users with devices.
        registration_ids = [self.friend1_device.registration_id]
        notif = ('{name} changed the location and time where {activity} is'
                 ' happening.').format(name=event.creator.name,
                                       activity=event.title)
        mock_apns.assert_any_call(registration_ids=registration_ids, alert=notif,
                                  badge=1)

        # It should init the Twilio client with the proper params.
        mock_twilio.assert_called_with(settings.TWILIO_ACCOUNT,
                                       settings.TWILIO_TOKEN)

        # It should send SMS to users without devices.
        phone = unicode(self.friend2_phone.phone)
        sms_extra = ' The location was removed. The new time is {date}.'.format(
                date=date)
        sms = notif + sms_extra + self.signature
        mock_client.messages.create.assert_called_with(to=phone, 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=sms)

        # It should return the event.
        serializer = EventSerializer(event)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    @mock.patch('down.apps.events.serializers.TwilioRestClient')
    def test_update_remove_place(self, mock_twilio, mock_apns):
        # Mock the Twilio SMS API.
        mock_client = mock.MagicMock()
        mock_twilio.return_value = mock_client

        data = {
            'title': self.event.title,
            'creator': self.event.creator_id,
            'canceled': self.event.canceled,
            'datetime': self.event.datetime.strftime(settings.DATETIME_FORMAT),
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should update the event.
        event = Event.objects.get(id=self.event.id)
        self.assertIsNone(event.place)

        # It should notify the users who haven't declined their invitation about
        # the changes.

        # It should send push notifications to users with devices.
        registration_ids = [self.friend1_device.registration_id]
        notif = ('{name} removed the location where {activity} is'
                 ' happening.').format(name=event.creator.name,
                                       activity=event.title)
        mock_apns.assert_any_call(registration_ids=registration_ids, alert=notif,
                                  badge=1)

        # It should init the Twilio client with the proper params.
        mock_twilio.assert_called_with(settings.TWILIO_ACCOUNT,
                                       settings.TWILIO_TOKEN)

        # It should send SMS to users without devices.
        phone = unicode(self.friend2_phone.phone)
        sms_extra = ''
        sms = notif + sms_extra + self.signature
        mock_client.messages.create.assert_called_with(to=phone, 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=sms)

        # It should return the event.
        serializer = EventSerializer(event)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    @mock.patch('down.apps.events.serializers.TwilioRestClient')
    @mock.patch('down.apps.events.serializers.get_event_date')
    def test_update_datetime(self, mock_date, mock_twilio, mock_apns):
        # Mock the Twilio SMS API.
        mock_client = mock.MagicMock()
        mock_twilio.return_value = mock_client

        coords = self.place.geo.coords
        data = {
            'title': self.event.title,
            'creator': self.event.creator_id,
            'canceled': self.event.canceled,
            'place': {
                'name': self.place.name,
                'geo': 'POINT({lat} {lng})'.format(lat=coords[0], lng=coords[1]),
            },
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should update the event.
        event = Event.objects.get(id=self.event.id)
        self.assertIsNone(event.datetime)

        # It should notify the users who haven't declined their invitation about
        # the changes.

        # It should send push notifications to users with devices.
        registration_ids = [self.friend1_device.registration_id]
        notif = ('{name} removed the time when {activity} is happening.').format(
                name=event.creator.name, activity=event.title)
        mock_apns.assert_any_call(registration_ids=registration_ids, alert=notif,
                                  badge=1)

        # It should init the Twilio client with the proper params.
        mock_twilio.assert_called_with(settings.TWILIO_ACCOUNT,
                                       settings.TWILIO_TOKEN)

        # It should send SMS to users without devices.
        phone = unicode(self.friend2_phone.phone)
        sms_extra = ''
        sms = notif + sms_extra + self.signature
        mock_client.messages.create.assert_called_with(to=phone, 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=sms)

        # It should return the event.
        serializer = EventSerializer(event)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    @mock.patch('down.apps.events.serializers.TwilioRestClient')
    def test_update_remove_place_and_datetime(self, mock_twilio, mock_apns):
        # Mock the Twilio SMS API.
        mock_client = mock.MagicMock()
        mock_twilio.return_value = mock_client

        # Send data without a place or datetime.
        data = {
            'title': self.event.title,
            'creator': self.event.creator_id,
            'canceled': self.event.canceled,
        }
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should update the event by removing the place and datetime.
        event = Event.objects.get(id=self.event.id)
        self.assertIsNone(event.place)
        self.assertIsNone(event.datetime)

        # It should notify the users who haven't declined their invitation about
        # the changes.

        # It should send push notifications to users with devices.
        registration_ids = [self.friend1_device.registration_id]
        notif = ('{name} removed the location and time where {activity} is'
                 ' happening.').format(name=event.creator.name,
                                       activity=event.title)
        mock_apns.assert_any_call(registration_ids=registration_ids, alert=notif,
                                  badge=1)

        # It should init the Twilio client with the proper params.
        mock_twilio.assert_called_with(settings.TWILIO_ACCOUNT,
                                       settings.TWILIO_TOKEN)

        # It should send SMS to users without devices.
        phone = unicode(self.friend2_phone.phone)
        sms_extra = ''
        sms = notif + sms_extra + self.signature
        mock_client.messages.create.assert_called_with(to=phone, 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=sms)

        # It should return the event.
        serializer = EventSerializer(event)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    @mock.patch('down.apps.events.serializers.TwilioRestClient')
    @mock.patch('down.apps.events.serializers.get_event_date')
    def test_update_add_place_and_datetime(self, mock_date, mock_twilio,
                                           mock_apns):
        # Mock the localized date string.
        date = 'Thursday, Jun. 4 @ 6 PM'
        mock_date.return_value = date

        # Mock the Twilio SMS API.
        mock_client = mock.MagicMock()
        mock_twilio.return_value = mock_client

        # Mock the event having no place or datetime.
        self.event.place = None
        self.event.datetime = None
        self.event.save()

        dt = timezone.now()
        data = {
            'title': self.event.title,
            'creator': self.event.creator_id,
            'canceled': self.event.canceled,
            'datetime': dt.strftime(settings.DATETIME_FORMAT),
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
        self.assertEqual(event.datetime, dt)

        # It should notify the users who haven't declined their invitation about
        # the changes.

        # It should send push notifications to users with devices.
        registration_ids = [self.friend1_device.registration_id]
        notif = ('{name} changed the location and time where {activity} is'
                 ' happening.').format(name=event.creator.name,
                                       activity=event.title)
        mock_apns.assert_any_call(registration_ids=registration_ids, alert=notif,
                                  badge=1)

        # It should init the Twilio client with the proper params.
        mock_twilio.assert_called_with(settings.TWILIO_ACCOUNT,
                                       settings.TWILIO_TOKEN)

        # It should send SMS to users without devices.
        phone = unicode(self.friend2_phone.phone)
        sms_extra = (' The new location is {place}, and the new time is'
                     ' {date}.').format(place=place.name, date=date)
        sms = notif + sms_extra + self.signature
        mock_client.messages.create.assert_called_with(to=phone, 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=sms)

        # It should return the event.
        serializer = EventSerializer(event)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_update_not_creator(self, mock_apns):
        # Log another user who was invited to the event in.
        token = Token(user=self.friend1)
        token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token '+token.key)

        response = self.client.put(self.detail_url, None, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    @mock.patch('django.utils.timezone.now')
    def test_create_message(self, mock_now, mock_send):
        # Re-save the event after we've mocked the current time so that the
        # event's updated_at time is what we expect.
        now = pytz.utc.localize(datetime.now())
        mock_now.return_value = now
        self.event.save()

        # Make now return a greater time so that when we update the event, the
        # event's updated_at time is greater.
        updated_at = pytz.utc.localize(datetime.now() + timedelta(seconds=1))
        mock_now.return_value = updated_at

        # Mark friend2 as having posted a message in the event's group chat.
        self.friend2_invitation.to_user_messaged = True
        self.friend2_invitation.save()

        # Give friend2 a device so that we can send them a push notification.
        registration_id = ('3ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '10df230567037dcc4')
        device_id = 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F'
        friend2_device = APNSDevice(registration_id=registration_id,
                                    device_id=device_id, name='iPhone, 8.2',
                                    user=self.friend2)
        friend2_device.save()

        data = {'text': 'So down!'}
        response = self.client.post(self.create_message_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should notify users with devices who have accepted the invitation,
        # or who have posted a message in the group chat about the user's
        # message.
        tokens = [
            self.friend1_device.registration_id,
            friend2_device.registration_id,
        ]
        if len(self.event.title) > 25:
            activity = self.event.title[:25] + '...'
        else:
            activity = self.event.title
        message = '{name} to {activity}: {text}'.format(
                name=self.user.name, activity=activity, text=data['text'])
        mock_send.assert_any_call(registration_ids=tokens, alert=message)

        # It should set a flag on the invitation marking that the user has posted
        # a message in the group chat.
        invitation = Invitation.objects.get(id=self.user_invitation.id)
        self.assertTrue(invitation.to_user_messaged)

        # It should update the time the event was updated.
        event = Event.objects.get(id=self.event.id)
        self.assertEqual(event.updated_at, updated_at)

    def test_create_message_not_invited(self):
        # Uninvite the logged in user. (You can't actually do that)
        self.user_invitation.delete()
        
        data = {'text': 'So down!'}
        response = self.client.post(self.create_message_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    @mock.patch('down.apps.events.views.TwilioRestClient')
    def test_cancel(self, mock_twilio, mock_apns):
        # Mock the Twilio SMS API.
        mock_client = mock.MagicMock()
        mock_twilio.return_value = mock_client

        # Have the SMS user accept their invitation.
        self.friend2_invitation.response = Invitation.ACCEPTED
        self.friend2_invitation.save()

        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should set the event to canceled.
        event = Event.objects.get(id=self.event.id)
        self.assertTrue(event.canceled)

        # It should send push notifications to users with devices.
        registration_ids = [self.friend1_device.registration_id]
        notif = '{name} canceled {activity}'.format(name=event.creator.name,
                                                    activity=event.title)
        mock_apns.assert_any_call(registration_ids=registration_ids, alert=notif,
                                  badge=1)

        # It should init the Twilio client with the proper params.
        mock_twilio.assert_called_with(settings.TWILIO_ACCOUNT,
                                       settings.TWILIO_TOKEN)

        # It should send SMS to users without devices.
        phone = unicode(self.friend2_phone.phone)
        mock_client.messages.create.assert_called_with(to=phone, 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=notif)

        # It should return the event.
        serializer = EventSerializer(event)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)

    def test_get_invitations(self):
        response = self.client.get(self.invitations_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the invitations of users who are down or might be down.
        invitations = [self.user_invitation, self.friend1_invitation]
        serializer = EventInvitationSerializer(invitations, many=True)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)

    def test_get_invitations_not_member(self):
        # You should only be able to get the invitations for an event that you
        # are either down, or might be down for.
        self.user_invitation.response = Invitation.NO_RESPONSE
        self.user_invitation.save()

        response = self.client.get(self.invitations_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class InvitationTests(APITestCase):

    # We have to mock the function that sends push notifications, since 
    # inviting people to events will send push notifications.
    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def setUp(self, mock_send):
        self.patcher = mock.patch('requests.patch')
        self.mock_patch = self.patcher.start()

        # Mock a few users.
        self.user1 = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                          username='tdog')
        self.user1.save()
        self.user2 = User(email='jclarke@gmail.com', name='Joan Clarke',
                          username='jcke')
        self.user2.save()
        self.user3 = User(name='Bruce Lee') # SMS users don't have a username.
        self.user3.save()
        self.user4 = User(email='alovelace@gmail.com', name='Ada Lovely Lovelace',
                          username='alove')
        self.user4.save()

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

        registration_id = ('4ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '10df230567037dcc4')
        device_id = 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F'
        self.user4_device = APNSDevice(registration_id=registration_id,
                                       device_id=device_id, name='iPhone, 8.2',
                                       user=self.user4)
        self.user4_device.save()

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
        # TODO: Only send the to user and the event.
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
                {
                    'from_user': self.user1.id,
                    'to_user': self.user4.id,
                    'event': self.event.id,
                    'response': Invitation.NO_RESPONSE,
                },
            ],
        }

    def tearDown(self):
        self.patcher.stop()

    @mock.patch('down.apps.events.models.Invitation.objects.bulk_create')
    def test_bulk_create(self, mock_bulk_create):
        response = self.client.post(self.list_url, self.post_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should bulk create the invitations.
        # TODO: Make this test more robust.
        self.assertTrue(mock_bulk_create.called)

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

    @mock.patch('down.apps.events.serializers.add_member')
    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_accept(self, mock_send, mock_add_member):
        # Mock an invitation.
        invitation = Invitation(from_user=self.user1, to_user=self.user2,
                                event=self.event, response=Invitation.NO_RESPONSE)
        invitation.save()

        # Save the most recent time the event was updated.
        updated_at = self.event.updated_at

        url = reverse('invitation-detail', kwargs={'pk': invitation.id})
        data = {
            'from_user': invitation.from_user_id,
            'to_user': invitation.to_user_id,
            'event': invitation.event_id,
            'response': Invitation.ACCEPTED,
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should update the invitation.
        invitation = Invitation.objects.get(**data)

        # It should update the event.
        event = Event.objects.get(id=invitation.event_id)
        self.assertGreater(event.updated_at, updated_at)

        # It should add the user to the meteor server members list.
        mock_add_member.assert_called_once_with(event.id, invitation.to_user_id)

    @mock.patch('down.apps.events.serializers.add_member')
    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_maybe(self, mock_send, mock_add_member):
        # Mock an invitation.
        invitation = Invitation(from_user=self.user1, to_user=self.user2,
                                event=self.event, response=Invitation.NO_RESPONSE)
        invitation.save()

        # Save the most recent time the event was updated.
        updated_at = self.event.updated_at

        url = reverse('invitation-detail', kwargs={'pk': invitation.id})
        data = {
            'from_user': invitation.from_user_id,
            'to_user': invitation.to_user_id,
            'event': invitation.event_id,
            'response': Invitation.MAYBE,
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should update the invitation.
        invitation = Invitation.objects.get(**data)

        # It should update the event.
        event = Event.objects.get(id=invitation.event_id)
        self.assertGreater(event.updated_at, updated_at)

        # It should add the user to the meteor server members list.
        mock_add_member.assert_called_once_with(event.id, invitation.to_user_id)

    @mock.patch('down.apps.events.serializers.remove_member')
    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    def test_decline(self, mock_send, mock_remove_member):
        # Mock an invitation.
        invitation = Invitation(from_user=self.user1, to_user=self.user2,
                                event=self.event, response=Invitation.NO_RESPONSE)
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

        # It should add the user to the meteor server members list.
        mock_remove_member.assert_called_once_with(event.id, invitation.to_user_id)

    @mock.patch('down.apps.events.serializers.add_member')
    def test_accept_bad_meteor_response(self, mock_add_member):
        # Mock a bad response from the meteor server.
        mock_add_member.side_effect = requests.exceptions.HTTPError()

        # Mock an invitation.
        invitation = Invitation(from_user=self.user1, to_user=self.user2,
                                event=self.event, response=Invitation.NO_RESPONSE)
        invitation.save()

        url = reverse('invitation-detail', kwargs={'pk': invitation.id})
        data = {
            'from_user': invitation.from_user_id,
            'to_user': invitation.to_user_id,
            'event': invitation.event_id,
            'response': Invitation.ACCEPTED,
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code,
                         status.HTTP_503_SERVICE_UNAVAILABLE)

    @mock.patch('down.apps.events.serializers.remove_member')
    def test_decline_bad_meteor_response(self, mock_remove_member):
        # Mock a bad response from the meteor server.
        mock_remove_member.side_effect = requests.exceptions.HTTPError()

        # Mock an invitation.
        invitation = Invitation(from_user=self.user1, to_user=self.user2,
                                event=self.event, response=Invitation.NO_RESPONSE)
        invitation.save()

        url = reverse('invitation-detail', kwargs={'pk': invitation.id})
        data = {
            'from_user': invitation.from_user_id,
            'to_user': invitation.to_user_id,
            'event': invitation.event_id,
            'response': Invitation.DECLINED,
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code,
                         status.HTTP_503_SERVICE_UNAVAILABLE)


class SuggestedEventsTests(APITestCase):

    def test_get(self):
        url = reverse('suggested-events')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'suggested-events.html')


class LinkInvitationTests(APITestCase):

    def setUp(self):
        # Mock two users.
        self.user1 = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                          username='tdog')
        self.user1.save()

        self.user2 = User(email='rfeynman@gmail.com', name='Richard Feynman',
                          username='partickle')
        self.user2.save()

        # Authorize the requests with the first user's token.
        self.token = Token(user=self.user1)
        self.token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # Mock an event.
        self.event = Event(title='bars?!?!!', creator=self.user1)
        self.event.save()

        # Invite the first user to the event.
        self.invitation1 = Invitation(event=self.event, from_user=self.user1,
                                      to_user=self.user1,
                                      response=Invitation.ACCEPTED)
        self.invitation1.save()

        # Save URLs.
        self.list_url = reverse('link-invitation-list')

    def test_create(self):
        data = {
            'event': self.event.id,
            'from_user': self.user1.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create the link invitation.
        link_invitation = LinkInvitation.objects.get(event=self.event,
                                                     from_user=self.user1)

        # It should set a hashid on the link invitation.
        hashids = Hashids(salt=settings.HASHIDS_SALT, min_length=6)
        link_id = hashids.encode(data['event'], data['from_user'])
        self.assertEqual(link_invitation.link_id, link_id)

        # It should return the invitation.
        serializer = LinkInvitationSerializer(link_invitation)
        json_link_invitation = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_link_invitation)

    def test_create_not_invited(self):
        # Delete the user's invitation.
        self.invitation1.delete()

        data = {
            'event': self.event.id,
            'from_user': self.user1.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_not_logged_in(self):
        # Log the user out.
        self.client.credentials()

        data = {
            'event': self.event.id,
            'from_user': self.user1.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_already_exists(self):
        # Mock a link invitation.
        link_invitation = LinkInvitation(event=self.event, from_user=self.user1)
        link_invitation.save()

        data = {
            'event': self.event.id,
            'from_user': self.user1.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the invitation.
        serializer = LinkInvitationSerializer(link_invitation)
        json_link_invitation = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_link_invitation)

    def test_create_not_from_user(self):
        # Log in as the second user.
        self.token = Token(user=self.user2)
        self.token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        data = {
            'event': self.event.id,
            'from_user': self.user1.id,
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_by_link_id(self):
        # Mock a link invitation.
        link_invitation = LinkInvitation(event=self.event, from_user=self.user1)
        link_invitation.save()

        url = reverse('link-invitation-detail', kwargs={
            'link_id': link_invitation.link_id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the link invitation.
        serializer = LinkInvitationSerializer(link_invitation)
        json_link_invitation = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_link_invitation)
