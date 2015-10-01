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
from down.apps.auth.models import User, UserPhone
from down.apps.events.models import (
    Event,
    Invitation,
    LinkInvitation,
    Place,
)
from down.apps.events.serializers import (
    EventSerializer,
    InvitationSerializer,
    EventInvitationSerializer,
    UserInvitationSerializer,
    LinkInvitationFkObjectsSerializer,
    LinkInvitationSerializer,
)
from down.apps.friends.models import Friendship


class EventTests(APITestCase):

    def setUp(self):
        self.patcher = mock.patch('requests.patch')
        self.mock_patch = self.patcher.start()

        # Mock a user.
        self.user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                         username='tdog')
        self.user.save()

        # Mock two of the user's friend1s
        self.friend1 = User(email='jclarke@gmail.com', name='Joan Clarke',
                           username='jcke')
        self.friend1.save()

        # This user doesn't have the app yet, so they only have a name.
        self.friend2 = User(name='Richard Feynman')
        self.friend2.save()

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
        self.member_invitations_url = reverse('event-member-invitations', kwargs={
            'pk': self.event.id
        })
        self.invited_ids_url = reverse('event-invited-ids', kwargs={
            'pk': self.event.id
        })
    
    def tearDown(self):
        self.patcher.stop()

    @mock.patch('down.apps.events.serializers.add_member')
    @mock.patch('down.apps.events.serializers.send_message')
    def test_create(self, mock_send_message, mock_add_member):
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

        # It should create the invitations.
        Invitation.objects.get(to_user=self.user, from_user=self.user, event=event,
                               response=Invitation.ACCEPTED)
        Invitation.objects.get(to_user=self.friend1, from_user=self.user,
                               event=event, response=Invitation.NO_RESPONSE)

        # It should add the creator to the members list.
        mock_add_member.assert_called_once_with(event.id, event.creator_id)

        # It should send notifications to the users who were invited aside from
        # the creator.
        user_ids = [self.friend1.id]
        message = 'from {name}'.format(name=self.user.name)
        mock_send_message.assert_called_once_with(user_ids, message,
                                                  event_id=event.id,
                                                  from_user=self.user)

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

    @mock.patch('down.apps.events.views.send_message')
    def test_create_message(self, mock_send_message):
        # Accept the invitation.
        self.friend2_invitation.response = Invitation.ACCEPTED
        self.friend2_invitation.save()

        data = {'text': 'So down!'}
        response = self.client.post(self.create_message_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should notify users with devices who have accepted the invitation,
        # or who have posted a message in the group chat about the user's
        # message.
        user_ids = [self.friend1.id, self.friend2.id]
        if len(self.event.title) > 25:
            activity = self.event.title[:25] + '...'
        else:
            activity = self.event.title
        message = '{name} to {activity}: {text}'.format(
                name=self.user.name, activity=activity, text=data['text'])
        mock_send_message.assert_any_call(user_ids, message, sms=False)

    def test_create_message_not_invited(self):
        # Uninvite the logged in user. (You can't actually do that)
        self.user_invitation.delete()
        
        data = {'text': 'So down!'}
        response = self.client.post(self.create_message_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_member_invitations(self):
        response = self.client.get(self.member_invitations_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return users' who've responded accepted/maybe invitations.
        invitations = [
            self.user_invitation,
            self.friend1_invitation,
        ]
        serializer = EventInvitationSerializer(invitations, many=True)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)

    def test_get_invited_ids(self):
        response = self.client.get(self.invited_ids_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return a list of ids of the users who were invited to the
        # event.
        invited_users = [self.user, self.friend1, self.friend2]
        invited_ids = [user.id for user in invited_users]
        content = json.loads(response.content)
        self.assertEqual(content, invited_ids)


class InvitationTests(APITestCase):

    def setUp(self):
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
            'to_user': self.user2.id,
            'event': self.event.id,
        }
        self.bulk_create_data = {
            'event': self.event.id,
            'invitations': [
                {
                    'to_user': self.user2.id,
                },
                {
                    'to_user': self.user3.id,
                },
                {
                    'to_user': self.user4.id,
                },
            ],
        }

    def tearDown(self):
        self.patcher.stop()

    @mock.patch('down.apps.events.serializers.send_message')
    def test_bulk_create(self, mock_send_message):
        # Invite the current user.
        invitation = Invitation(to_user=self.user1, from_user=self.user1,
                                event=self.event, response=Invitation.MAYBE)
        invitation.save()

        response = self.client.post(self.list_url, self.bulk_create_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create the invitations.
        invitations = self.bulk_create_data['invitations']
        for invitation in invitations:
            Invitation.objects.get(to_user=invitation['to_user'],
                                   from_user=self.user1,
                                   event=self.event,
                                   response=Invitation.NO_RESPONSE)

        # It should send notifications to the users who were invited.
        # TODO: Include a link invitation.
        user_ids = [invitation['to_user'] for invitation in invitations]
        message = 'from {name}'.format(name=self.user1.name)
        mock_send_message.assert_called_once_with(user_ids, message,
                                                  event_id=self.event.id,
                                                  from_user=self.user1)

    def test_bulk_create_not_logged_in(self):
        # Don't include the user's credentials in the request.
        self.client.credentials()

        response = self.client.post(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @mock.patch('down.apps.events.serializers.send_message')
    def test_bulk_create_as_creator_not_invited(self, mock_send_message):
        response = self.client.post(self.list_url, self.bulk_create_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create the invitations.
        invitations = self.bulk_create_data['invitations']
        for invitation in invitations:
            Invitation.objects.get(to_user=invitation['to_user'],
                                   from_user=self.user1,
                                   event=self.event,
                                   response=Invitation.NO_RESPONSE)

        # It should send notifications to the users who were invited.
        # TODO: Include a link invitation.
        user_ids = [invitation['to_user'] for invitation in invitations]
        message = 'from {name}'.format(name=self.user1.name)
        mock_send_message.assert_called_once_with(user_ids, message,
                                                  event_id=self.event.id,
                                                  from_user=self.user1)

    def test_bulk_create_not_invited(self):
        # Log the second user in.
        token = Token(user=self.user2)
        token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token '+token.key)

        data = {
            'event': self.event.id,
            'invitations': [
                {
                    'to_user': self.user3.id,
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
            'event': event_id,
            'invitations': [
                {
                    'to_user': self.user1.id,
                }, 
            ],
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('down.apps.events.serializers.add_member')
    @mock.patch('down.apps.events.serializers.send_message')
    def test_accept(self, mock_send_message, mock_add_member):
        # Log in as user2.
        token = Token(user=self.user2)
        token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Mock invitations with every response.
        invitation1 = Invitation(from_user=self.user2, to_user=self.user1,
                                 event=self.event, response=Invitation.MAYBE)
        invitation1.save()
        invitation2 = Invitation(from_user=self.user2, to_user=self.user2,
                                 event=self.event, response=Invitation.MAYBE)
        invitation2.save()
        invitation3 = Invitation(from_user=self.user2, to_user=self.user3,
                                 event=self.event, response=Invitation.NO_RESPONSE)
        invitation3.save()
        invitation4 = Invitation(from_user=self.user2, to_user=self.user4,
                                 event=self.event, response=Invitation.ACCEPTED)
        invitation4.save()

        # Add user2 as a friend.
        friendship = Friendship(user=self.user1, friend=self.user2)
        friendship.save()
        friendship = Friendship(user=self.user4, friend=self.user2)
        friendship.save()

        url = reverse('invitation-detail', kwargs={'pk': invitation2.id})
        data = {
            'from_user': invitation2.from_user_id,
            'to_user': invitation2.to_user_id,
            'event': invitation2.event_id,
            'response': Invitation.ACCEPTED,
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should update the invitation.
        invitation = Invitation.objects.get(**data)

        # It should add the user to the meteor server members list.
        mock_add_member.assert_called_once_with(self.event.id,
                                                invitation.to_user_id)

        # It should notify users who are either down or might be down, and
        # haven't muted their notifications.
        user_ids = [self.user1.id, self.user4.id]
        message = '{name} is down for {event}'.format(
                name=self.user2.name,
                event=self.event.title)
        mock_send_message.assert_called_with(user_ids, message, sms=False)

    @mock.patch('down.apps.events.serializers.add_member')
    @mock.patch('down.apps.events.serializers.send_message')
    def test_maybe(self, mock_send_message, mock_add_member):
        # Log in as user2.
        token = Token(user=self.user2)
        token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Mock invitations with every response.
        invitation1 = Invitation(from_user=self.user1, to_user=self.user1,
                                 event=self.event, response=Invitation.MAYBE)
        invitation1.save()
        invitation2 = Invitation(from_user=self.user1, to_user=self.user2,
                                 event=self.event, response=Invitation.ACCEPTED)
        invitation2.save()
        invitation3 = Invitation(from_user=self.user1, to_user=self.user3,
                                 event=self.event, response=Invitation.NO_RESPONSE)
        invitation3.save()
        invitation4 = Invitation(from_user=self.user1, to_user=self.user4,
                                 event=self.event, response=Invitation.ACCEPTED)
        invitation4.save()

        # Add user2 as a friend.
        friendship = Friendship(user=self.user1, friend=self.user2)
        friendship.save()
        friendship = Friendship(user=self.user4, friend=self.user2)
        friendship.save()

        url = reverse('invitation-detail', kwargs={'pk': invitation2.id})
        data = {
            'from_user': invitation2.from_user_id,
            'to_user': invitation2.to_user_id,
            'event': invitation2.event_id,
            'response': Invitation.MAYBE,
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should update the invitation.
        invitation = Invitation.objects.get(**data)

        # It should add the user to the meteor server members list.
        mock_add_member.assert_called_once_with(self.event.id,
                                                invitation.to_user_id)

        # It should notify users who are either down or might be down, and
        # haven't muted their notifications.
        user_ids = [self.user1.id, self.user4.id, self.user1.id]
        message = '{name} might be down for {event}'.format(
                name=self.user2.name,
                event=self.event.title)
        mock_send_message.assert_called_with(user_ids, message, sms=False)

    @mock.patch('down.apps.events.serializers.remove_member')
    @mock.patch('down.apps.events.serializers.send_message')
    def test_decline(self, mock_send_message, mock_remove_member):
        # Mock an invitation.
        invitation = Invitation(from_user=self.user2, to_user=self.user1,
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
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should update the invitation.
        invitation = Invitation.objects.get(**data)

        # It should add the user to the meteor server members list.
        mock_remove_member.assert_called_once_with(self.event.id,
                                                   invitation.to_user)

        # It should notify the person who invited them.
        user_ids = [self.user2.id] # from_user
        message = '{name} can\'t make it to {event}'.format(
                name=self.user1.name,
                event=self.event.title)
        mock_send_message.assert_called_with(user_ids, message, sms=False)

    @mock.patch('down.apps.events.serializers.remove_member')
    @mock.patch('down.apps.events.serializers.send_message')
    def test_accept_then_decline(self, mock_send_message, mock_remove_member):
        # Log in as user3.
        token = Token(user=self.user3)
        token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Mock invitations.
        invitation1 = Invitation(from_user=self.user2, to_user=self.user1,
                                 event=self.event, response=Invitation.MAYBE)
        invitation1.save()
        invitation2 = Invitation(from_user=self.user2, to_user=self.user2,
                                 event=self.event, response=Invitation.NO_RESPONSE)
        invitation2.save()
        invitation3 = Invitation(from_user=self.user2, to_user=self.user3,
                                 event=self.event, response=Invitation.MAYBE)
        invitation3.save()
        invitation4 = Invitation(from_user=self.user2, to_user=self.user4,
                                 event=self.event, response=Invitation.ACCEPTED)
        invitation4.save()

        # Add user2 as a friend.
        friendship = Friendship(user=self.user1, friend=self.user3)
        friendship.save()
        friendship = Friendship(user=self.user4, friend=self.user3)
        friendship.save()

        url = reverse('invitation-detail', kwargs={'pk': invitation3.id})
        data = {
            'from_user': invitation3.from_user_id,
            'to_user': invitation3.to_user_id,
            'event': invitation3.event_id,
            'response': Invitation.DECLINED,
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should update the invitation.
        invitation = Invitation.objects.get(**data)

        # It should add the user to the meteor server members list.
        mock_remove_member.assert_called_once_with(self.event.id,
                                                   invitation.to_user)

        # It should notify users who are either down or might be down, and
        # haven't muted their notifications.
        user_ids = [self.user1.id, self.user4.id, self.user2.id]
        message = '{name} can\'t make it to {event}'.format(
                name=self.user3.name,
                event=self.event.title)
        mock_send_message.assert_called_with(user_ids, message, sms=False)

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

    def test_get_user_invitations(self):
        # Delete the user's invitation to avoid a duplicate invitation.
        to_friend_invitation = Invitation(from_user=self.user1, to_user=self.user2,
                                          event=self.event)
        to_friend_invitation.save()
        from_friend_invitation = Invitation(from_user=self.user2,
                                            to_user=self.user1, event=self.event)
        from_friend_invitation.save()

        user_invitations_url = '{list_url}?user={user_id}'.format(
                list_url=self.list_url, user_id=self.user2.id)
        response = self.client.get(user_invitations_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the invitations to/from the user.
        invitations = [to_friend_invitation, from_friend_invitation]
        serializer = UserInvitationSerializer(invitations, many=True)
        json_invitations = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_invitations)

    def test_get_user_invitations_no_user(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


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
        # Delete the user's invitation to make sure that we create it.
        Invitation.objects.filter(event=self.event, to_user=self.user1).delete()

        # Mock a link invitation.
        link_invitation = LinkInvitation(event=self.event, from_user=self.user1)
        link_invitation.save()

        url = reverse('link-invitation-detail', kwargs={
            'link_id': link_invitation.link_id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should create an invitation.
        Invitation.objects.get(from_user=link_invitation.from_user,
                               to_user=self.user1, event=link_invitation.event)

        # It should return the link invitation.
        link_invitation = LinkInvitation.objects.get(id=link_invitation.id)
        to_user = User.objects.get(id=self.user1.id)
        context = {'to_user': to_user}
        serializer = LinkInvitationFkObjectsSerializer(link_invitation,
                                                       context=context)
        json_link_invitation = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_link_invitation)

    def test_get_by_link_id_anon(self):
        # Log the user out.
        self.client.credentials()

        # Delete the user's invitation to make sure that we don't create it.
        Invitation.objects.filter(event=self.event, to_user=self.user1).delete()

        # Mock a link invitation.
        link_invitation = LinkInvitation(event=self.event, from_user=self.user1)
        link_invitation.save()

        url = reverse('link-invitation-detail', kwargs={
            'link_id': link_invitation.link_id,
        })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the link invitation.
        link_invitation = LinkInvitation.objects.get(id=link_invitation.id)
        serializer = LinkInvitationFkObjectsSerializer(link_invitation)
        json_link_invitation = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_link_invitation)

    # TODO: test_get_by_link_id_already_invited
