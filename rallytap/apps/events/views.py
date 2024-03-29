from __future__ import unicode_literals
from django.conf import settings
from django.contrib.gis.measure import D
from django.db.models import F, Q
from django.views.generic.base import TemplateView
import requests
from rest_framework import authentication, mixins, status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .filters import NearbyPlaceFilter
from .models import Event, RecommendedEvent, SavedEvent
from .permissions import IsCreator
from .serializers import (
    CommentSerializer,
    EventSerializer,
    RecommendedEventSerializer,
    SavedEventSerializer,
    SavedEventFullEventSerializer,
)
from rallytap.apps.auth.models import User, Points
from rallytap.apps.auth.permissions import IsMeteor
from rallytap.apps.auth.serializers import FriendSerializer
from rallytap.apps.events.models import Event
from rallytap.apps.friends.models import Friendship
from rallytap.apps.notifications.utils import send_message
from rallytap.apps.utils.exceptions import ServiceUnavailable
from rallytap.apps.utils.utils import add_members


class EventViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin,
                   mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsCreator)
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def create(self, request, *args, **kwargs):
        # Set the event creator to be the current user.
        request.data['creator'] = request.user.id

        return super(EventViewSet, self).create(request, *args, **kwargs)

    @detail_route(methods=['get'])
    def interested(self, request, pk=None):
        # Make sure the user has saved the event.
        if SavedEvent.objects.filter(user=request.user, event_id=pk).count() == 0:
            raise PermissionDenied('You aren\'t interested in this event, yet.')

        users = [saved_event.user
                 for saved_event in SavedEvent.objects.filter(event_id=pk) \
                         .exclude(user=request.user.id)]
        serializer = FriendSerializer(users, many=True)
        return Response(serializer.data)

    @detail_route(methods=['post'], permission_classes=(IsMeteor,))
    def comment(self, request, pk=None):
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid()

        event = self.get_object()
        from_user = User.objects.get(id=serializer.data['from_user'])
        to_users_ids = [saved_event.user_id
                        for saved_event in SavedEvent.objects.filter(event=event) \
                                .exclude(user=from_user)]
        message = '{name} to {activity}: {text}'.format(name=from_user.name,
                activity=event.title, text=serializer.data['text'])
        send_message(to_users_ids, message)

        return Response()


class RecommendedEventViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = RecommendedEvent.objects.all()
    serializer_class = RecommendedEventSerializer
    filter_backends = (NearbyPlaceFilter,)


class SavedEventViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = SavedEvent.objects.all()
    serializer_class = SavedEventSerializer

    def create(self, request, *args, **kwargs):
        data = dict(request.data)
        data['user'] = request.user.id
        data['location'] = request.user.location

        serializer = SavedEventSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Make sure the user has access to this event.
        friendships = Friendship.objects.filter(user=request.user)
        friends_ids = set(friendships.values_list('friend_id', flat=True))
        event_id = serializer.data['event']
        event = Event.objects.get(id=event_id)
        friends_saved_events = SavedEvent.objects.filter(event_id=event_id,
                                                         user__in=friends_ids)
        saved_event_friends_ids = [saved_event.user_id
                                   for saved_event in friends_saved_events]
        if (not event.creator_id == request.user.id and
            (friends_saved_events.count() == 0 or
             (event.friends_only and event.creator_id not in friends_ids))):
            raise PermissionDenied('You don\'t have access to that event.')

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Add the creator to the meteor server members list.
        try:
            add_members(event, request.user.id)
        except requests.exceptions.HTTPError:
            raise ServiceUnavailable()

        # Notify the user's friends who are also interested.
        message = '{name} is also interested in {activity}!'.format(
                name=request.user.name, activity=event.title)
        send_message(saved_event_friends_ids, message)

        # Give the user points!
        request.user.points += Points.SAVED_EVENT
        request.user.save()

        # Give the user who created the event points!
        if event.creator_id != request.user.id:
            creator = event.creator
            creator.points += Points.SAVED_EVENT
            creator.save()

        # See how many users are interested in this event. Convert the queryset
        # to a list so that it's only evaluated once.
        saved_events = list(SavedEvent.objects.filter(event_id=event_id))
        total_num_interested = {event_id: len(saved_events)}

        # See which of the user's friends are interested in this event.
        friends_dict = {
            friendship.friend_id: friendship.friend
            for friendship in friendships
        }
        interested_friends = {
            event_id: [friends_dict[saved_event.user_id]
                       for saved_event in saved_events
                       if friends_dict.has_key(saved_event.user_id)]
        }

        # Since creating the saved event removes any context from the serializer,
        # we have to serialize the saved event again with the user's connections
        # who are also interested.
        context = {
            'interested_friends': interested_friends,
            'total_num_interested': total_num_interested,
        }
        saved_event = serializer.instance
        # We have to get the event because right now it's a pk-only object.
        saved_event.event = Event.objects.get(id=saved_event.event_id)
        serializer = SavedEventFullEventSerializer(saved_event, context=context)

        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)

    def list(self, request, *args, **kwargs):
        """
        Return saved events that fulfill any of the following criteria:

        - The user saved the event.
        - The user's friend saved the event, and the event is nearby.
        - The user's friend saved the event, and the friend was nearby when they
          saved the event.

        Only return saved events where the event hasn't expired yet.

        If multiple of the user's friends have saved the event, only return the
        saved event that was created first.
        """
        user_ids = [friendship.friend
                for friendship in Friendship.objects.filter(user=request.user)]
        user_ids.append(request.user.id)
        user_location = request.user.location
        center = request.user.location
        radius = settings.NEARBY_RADIUS
        nearby_circle = center.buffer(radius)
        saved_events_qs = SavedEvent.objects.filter(user_id__in=user_ids) \
                .select_related('event') \
                .filter(event__expired=False) \
                .select_related('event__place') \
                .filter(
                    Q(user=request.user) |
                    Q(location__contained=nearby_circle) |
                    (Q(event__place__isnull=False) &
                     Q(event__place__geo__contained=nearby_circle))) \
                .exclude(
                    Q(event__friends_only=True) &
                    ~Q(event__creator_id=request.user.id) &
                    ~Q(event__creator_id=F('user_id')))
                # TODO: don't return friends only events created by the user's
                # friend who hasn't added them back.

        # Filter out duplicates.
        unique_saved_events = {}
        for saved_event in saved_events_qs:
            event = saved_event.event
            if (not unique_saved_events.has_key(event.id) or
                    unique_saved_events[event.id].created_at > event.created_at):
                unique_saved_events[event.id] = saved_event
        saved_events = [saved_event for saved_event in saved_events_qs
                if unique_saved_events.has_key(saved_event.event_id)
                and unique_saved_events[saved_event.event_id].id == saved_event.id]

        # Sort the saved events from newest to oldest.
        saved_events.sort(lambda a, b: 1 if a.created_at < b.created_at else -1)

        # Get the users who are interested in each event that the user is interested
        # in.
        interested_friends = {}
        friend_ids = set()
        for saved_event in saved_events_qs:
            friend_ids.add(saved_event.user_id)
        # Convert the queryset into a list to evaluate the queryset.
        # TODO: Double check that this is necessary.
        friends = list(User.objects.filter(id__in=friend_ids) \
                .exclude(id=request.user.id))
        friends_dict = {friend.id: friend for friend in friends}
        for saved_event in saved_events:
            # Only set the interested friends if the user has saved the event.
            if saved_events_qs.filter(user_id=request.user.id,
                                      event_id=saved_event.event_id) \
                    .count() == 0:
                continue

            this_event_saved_events = saved_events_qs.filter(
                    event_id=saved_event.event_id)
            this_event_interested_friends = [friends_dict[_saved_event.user_id]
                    for _saved_event in this_event_saved_events
                    if _saved_event.user_id != request.user.id]
            interested_friends[saved_event.event_id] = this_event_interested_friends

        # Get the total number of people who are interested in each event.
        event_ids = [saved_event.event_id for saved_event in saved_events]
        # Make the result a list to evaluate the queryset.
        all_saved_events = list(SavedEvent.objects.filter(
                event_id__in=event_ids))
        total_num_interested = {
            saved_event.event_id: len([
                _saved_event for _saved_event in all_saved_events
                if _saved_event.event_id == saved_event.event_id
            ])
            for saved_event in saved_events
        }

        context = {
            'interested_friends': interested_friends,
            'total_num_interested': total_num_interested,
        }
        serializer = SavedEventFullEventSerializer(data=saved_events, many=True,
                                                   context=context)
        serializer.is_valid()
        return Response(serializer.data)
