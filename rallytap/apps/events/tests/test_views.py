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
from rallytap.apps.auth.serializers import FriendSerializer
from rallytap.apps.events.models import Event, Place, RecommendedEvent, SavedEvent
from rallytap.apps.events.serializers import (
    EventSerializer,
    RecommendedEventSerializer,
    SavedEventSerializer,
    SavedEventFullEventSerializer,
)
from rallytap.apps.friends.models import Friendship


class EventTests(APITestCase):

    def setUp(self):
        # Mock a user.
        self.user = User(location='POINT(40.6898319 -73.9904645)')
        self.user.save()

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

        # Mock the user's friend.
        self.friend = User()
        self.friend.save()
        friendship = Friendship(user=self.friend, friend=self.user)
        friendship.save()
        friendship = Friendship(user=self.user, friend=self.friend)
        friendship.save()

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
        self.interested_url = reverse('event-interested', kwargs={
            'pk': self.event.id,
        })
        self.comment_url = reverse('event-comment', kwargs={
            'pk': self.event.id,
        })

    @mock.patch('rallytap.apps.events.serializers.send_message')
    @mock.patch('rallytap.apps.events.serializers.add_members')
    def test_create(self, mock_add_members, mock_send_message):
        data = self.post_data
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create the place.
        place = data.pop('place')
        Place.objects.get(**place)

        # It should create the event.
        event = Event.objects.get(**data)

        # It should send notifications to the users who have added the creator as
        # a friend.
        user_ids = [self.friend.id]
        message = 'Your friend posted "{title}". Are you interested?'.format(
                name=self.user.name, title=event.title)
        self.assertEqual(mock_send_message.call_count, 1)
        args = mock_send_message.call_args[0]
        self.assertEqual(len(args), 2)
        self.assertListEqual(list(args[0]), user_ids)
        self.assertEqual(args[1], message)

        # It should save the event for the user.
        SavedEvent.objects.get(event=event, user=self.user,
                               location=self.user.location)

        # It should add the user to the members list on meteor.
        mock_add_members.assert_called_with(event, self.user.id)

        # It should return the event.
        serializer = EventSerializer(event)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)

    @mock.patch('rallytap.apps.events.serializers.send_message')
    @mock.patch('rallytap.apps.events.serializers.add_members')
    def test_create_friends_only(self, mock_add_members, mock_send_message):
        # Mock the user's friend who added the the user, but the user hasn't added
        # back.
        added_me = User()
        added_me.save()
        friendship = Friendship(user=added_me, friend=self.user)
        friendship.save()

        data = self.post_data
        data['friends_only'] = True
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create the place.
        place = data.pop('place')
        Place.objects.get(**place)

        # It should create the event.
        event = Event.objects.get(**data)

        # It should send notifications to the users who have added the creator as
        # a friend, and the creator has added back.
        user_ids = [self.friend.id]
        message = 'Your friend posted "{title}". Are you interested?'.format(
                name=self.user.name, title=event.title)
        self.assertEqual(mock_send_message.call_count, 1)
        args = mock_send_message.call_args[0]
        self.assertEqual(len(args), 2)
        self.assertListEqual(list(args[0]), user_ids)
        self.assertEqual(args[1], message)

        # It should save the event for the user.
        SavedEvent.objects.get(event=event, user=self.user,
                               location=self.user.location)

        # It should add the user to the members list on meteor.
        mock_add_members.assert_called_with(event, self.user.id)

        # It should return the event.
        serializer = EventSerializer(event)
        json_event = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_event)

    def test_create_not_logged_in(self):
        # Don't include the user's credentials in the request.
        self.client.credentials()

        response = self.client.post(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @mock.patch('rallytap.apps.events.serializers.send_message')
    @mock.patch('rallytap.apps.events.serializers.add_members')
    def test_create_add_members_error(self, mock_add_members, mock_send_message):
        mock_add_members.side_effect = requests.exceptions.HTTPError()

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

    def test_interested(self):
        # Mock the user and their friend having saved the event.
        user_saved_event = SavedEvent(user=self.user, event=self.event,
                                      location=self.user.location)
        user_saved_event.save()
        friend_saved_event = SavedEvent(user=self.friend, event=self.event,
                                        location=self.user.location)
        friend_saved_event.save()

        response = self.client.get(self.interested_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the user's friend.
        users = [self.friend]
        serializer = FriendSerializer(users, many=True)
        json_users = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_users)

    def test_interested_not_interested(self):
        # Make sure the user isn't interested in the event.
        with self.assertRaises(SavedEvent.DoesNotExist):
            SavedEvent.objects.get(event=self.event, user=self.user)

        response = self.client.get(self.interested_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @mock.patch('rallytap.apps.events.views.send_message')
    def test_comment(self, mock_send_message):
        # Use the meteor server's auth token.
        dt = timezone.now()
        meteor_user = User(id=settings.METEOR_USER_ID, date_joined=dt)
        meteor_user.save()
        token = Token(user=meteor_user)
        token.save()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Mock the user and their friend having saved the event.
        user_saved_event = SavedEvent(user=self.user, event=self.event,
                                      location=self.user.location)
        user_saved_event.save()
        friend_saved_event = SavedEvent(user=self.friend, event=self.event,
                                        location=self.user.location)
        friend_saved_event.save()

        data = {
            'from_user': self.user.id,
            'text': 'Let\'s dooo it!',
        }
        response = self.client.post(self.comment_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should send the friend a push notification.
        user_ids = [self.friend.id]
        message = '{name} to {activity}: {text}'.format(name=self.user.name,
                activity=self.event.title, text=data['text'])
        mock_send_message.assert_called_once_with(user_ids, message)

    def test_comment_not_meteor(self):
        # Don't use the meteor server's auth token.
        response = self.client.post(self.comment_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


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


class SavedEventTests(APITestCase):

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

    @mock.patch('rallytap.apps.events.views.add_members')
    @mock.patch('rallytap.apps.events.views.send_message')
    def test_create(self, mock_send_message, mock_add_members):
        # Mock the user's friend.
        friend = User(name='Michael Bolton')
        friend.save()
        friendship = Friendship(user=self.user, friend=friend)
        friendship.save()

        # Mock an event.
        event = Event(title='get jiggy with it', creator=friend)
        event.save()
        friend_saved_event = SavedEvent(event=event, user=friend,
                                        location=self.user.location)
        friend_saved_event.save()

        # Mock another user who the user isn't friends with being interested, too.
        other_dude = User(name='Jazzy Jeff')
        other_dude.save()
        other_dude_saved_event = SavedEvent(event=event, user=other_dude,
                                            location=self.user.location)
        other_dude_saved_event.save()

        # Save the user's current score to compare to after the request.
        user_points = self.user.points

        # Save the friend's current score to compare to after the request.
        friend_points = friend.points

        data = {'event': event.id}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # It should create the saved event.
        saved_event = SavedEvent.objects.get(user=self.user, event=event,
                                             location=self.user.location)

        # It should add the user to the members list on meteor.
        mock_add_members.assert_called_once_with(event, self.user.id)

        # It should notify the user's friends who are already interested.
        friends = [friend.id]
        message = '{name} is also interested in {activity}!'.format(
                name=self.user.name, activity=event.title)
        mock_send_message.assert_called_once_with([friend.id], message)

        # It should give the user points!
        user = User.objects.get(id=self.user.id)
        self.assertEqual(user.points, user_points+Points.SAVED_EVENT)

        # It should give the user who created the event points!
        friend = User.objects.get(id=friend.id)
        self.assertEqual(friend.points, friend_points+Points.SAVED_EVENT)

        # It should return the saved event with your friends who have already saved
        # the event nested inside the event.
        context = {
            'interested_friends': {
                event.id: [friend],
            },
            'total_num_interested': {
                event.id: 3,
            },
        }
        serializer = SavedEventFullEventSerializer(saved_event, context=context)
        json_saved_events = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_saved_events)

    def test_create_not_logged_in(self):
        # Don't include the user's credentials in the request.
        self.client.credentials()

        response = self.client.post(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_friend_hasnt_saved_event(self):
        # Mock someone who the user isn't friends with creating/saving the event.
        non_connection = User()
        non_connection.save()
        event = Event(title='get jiggy with it', creator=non_connection)
        event.save()
        saved_event = SavedEvent(user=non_connection, event=event,
                                 location=self.user.location)
        saved_event.save()

        data = {'event': event.id}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_non_connection(self):
        # Mock someone who the user isn't connected to creating/saving a friends
        # only event.
        non_connection = User()
        non_connection.save()
        event = Event(title='get jiggy with it', creator=non_connection,
                      friends_only=True)
        event.save()
        saved_event = SavedEvent(user=non_connection, event=event,
                                 location=self.user.location)
        saved_event.save()

        # Mock the user's friend saving the event.
        friend = User(name='Michael Bolton')
        friend.save()
        friendship = Friendship(user=self.user, friend=friend)
        friendship.save()
        saved_event = SavedEvent(user=friend, event=event,
                                 location=self.user.location)
        saved_event.save()

        data = {'event': event.id}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @mock.patch('rallytap.apps.events.views.add_members')
    def test_create_add_members_error(self, mock_add_members):
        mock_add_members.side_effect = requests.exceptions.HTTPError()

        # Mock an event the user is saving.
        event = Event(title='get jiggy with it', creator=self.user)
        event.save()

        data = {'event': event.id}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_list(self):
        # Mock the user's friend.
        friend = User(name='Whitney Houston')
        friend.save()
        friendship = Friendship(user=self.user, friend=friend)
        friendship.save()

        # Mock the user's friend's friend.
        friend_of_friend = User(name='Jimmy Fallon')
        friend_of_friend.save()
        friendship = Friendship(user=friend, friend=friend_of_friend)
        friendship.save()

        # Save locations relative to the user's location.
        nearby_location = self.user.location
        far_location = Point(40.8560079, -73.970945)

        # Mock a nearby event that the user's friend is interested in.
        place = Place(name='the den', geo=nearby_location)
        place.save()
        nearby_event = Event(title='smokin dope', creator=friend_of_friend,
                             place=place)
        nearby_event.save()
        nearby_event_saved_event = SavedEvent(user=friend, event=nearby_event,
                                              location=far_location)
        nearby_event_saved_event.save()

        # Have the user be interested in the nearby event so that they get back
        # their friends who are also interested in the event.
        user_also_saved_event = SavedEvent(user=self.user, event=nearby_event,
                                           location=far_location)
        user_also_saved_event.save()

        # Have another of the user's friends save the nearby event, too, so that
        # we can make sure we're only returning the first of the user's friends'
        # saved events.
        other_friend = User(name='Jimmy Page')
        other_friend.save()
        friendship = Friendship(user=self.user, friend=other_friend)
        friendship.save()
        other_friend_saved_event = SavedEvent(user=other_friend,
                                              event=nearby_event,
                                              location=nearby_location)
        other_friend_saved_event.save()

        # Mock a far event that the user's nearby friend is interested in.
        place = Place(name='my crib', geo=far_location)
        place.save()
        nearby_user_event = Event(title='netflix and chill',
                                  creator=friend_of_friend,
                                  place=place)
        nearby_user_event.save()
        nearby_user_saved_event = SavedEvent(user=friend, event=nearby_user_event,
                                             location=nearby_location)
        nearby_user_saved_event.save()

        # Mock a far event that the user's far away friend is interested in.
        place = Place(name='rucker park', geo=far_location)
        place.save()
        far_event = Event(title='ballllinnnn', creator=friend_of_friend,
                          place=place)
        far_event.save()
        far_event_saved_event = SavedEvent(user=friend, event=far_event,
                                           location=far_location)
        far_event_saved_event.save()

        # Mock an event without a place that the user's friend is interested in.
        no_place_event = Event(title='the word game', creator=friend_of_friend)
        no_place_event.save()
        no_place_saved_event = SavedEvent(user=friend, event=no_place_event,
                                          location=far_location)
        no_place_saved_event.save()

        # Mock a friends_only event that the user's friend's friend created.
        friends_only_event = Event(title='being clicky', creator=friend_of_friend,
                                   friends_only=True)
        friends_only_event.save()
        friends_only_saved_event = SavedEvent(user=friend,
                                              event=friends_only_event,
                                              location=nearby_location)
        friends_only_saved_event.save()

        # Mock a saved event that the user saved.
        far_place = Place(name='the bean', geo=far_location)
        far_place.save()
        user_event = Event(title='coding up a storm', creator=friend,
                           place=far_place)
        user_event.save()
        user_saved_event = SavedEvent(user=self.user, event=user_event,
                                      location=far_location)
        user_saved_event.save()

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Mock a saved event where the event is expired.
        nearby_place = Place(name='mi casa', geo=nearby_location)
        nearby_place.save()
        sixty_nine = datetime(year=1969, month=7, day=20, hour=20, minute=18)
        expired_event = Event(title='watch the first moon landing',
                              creator=friend, datetime=sixty_nine, expired=True)
        expired_event.save()
        expired_event_saved_event = SavedEvent(event=expired_event, user=friend,
                                               location=nearby_location)
        expired_event_saved_event.save()

        # It should return the not-friends-only saved events, where either the
        # user is nearby, or the event is nearby. The saved events should be sorted
        # from newest to oldest.
        saved_events = [
            user_saved_event,
            nearby_user_saved_event,
            nearby_event_saved_event,
        ]
        context = {
            'interested_friends': {
                nearby_event.id: [friend, other_friend],
                user_event.id: [],
            },
            'total_num_interested': {
                nearby_event.id: 3,
                nearby_user_event.id: 1,
                user_event.id: 1,
            },
        }
        serializer = SavedEventFullEventSerializer(saved_events, many=True,
                                                   context=context)
        json_saved_events = JSONRenderer().render(serializer.data)
        self.assertEqual(response.content, json_saved_events)
