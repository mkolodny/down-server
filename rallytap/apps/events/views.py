from __future__ import unicode_literals
from django.conf import settings
from django.contrib.gis.measure import D
from django.db.models import F, Q
from django.views.generic.base import TemplateView
import requests
from rest_framework import authentication, mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .filters import NearbyPlaceFilter
from .models import Event, RecommendedEvent, SavedEvent
from .permissions import IsCreator
from .serializers import (
    EventSerializer,
    RecommendedEventSerializer,
    SavedEventSerializer,
)
from rallytap.apps.auth.models import User, Points
from rallytap.apps.events.models import Event
from rallytap.apps.friends.models import Friendship
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
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Add the creator to the meteor server members list.
        event_id = serializer.data['event']
        try:
            add_members(event_id, request.user.id)
        except requests.exceptions.HTTPError:
            raise ServiceUnavailable()

        # Give the user points!
        request.user.points += Points.SAVED_EVENT
        request.user.save()

        # Give the user who created the event points!
        event = Event.objects.get(id=event_id)
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
            for friendship in Friendship.objects.filter(user=request.user)
        }
        interested_friends = {
            event_id: [friends_dict[saved_event.user_id]
                       for saved_event in saved_events
                       if friends_dict.has_key(saved_event.user_id)]
        }

        # Also save how many of the user's friends are interested in this event.
        num_interested_friends = {event_id: len(interested_friends)}

        # Since creating the saved event removes any context from the serializer,
        # we have to serialize the saved event again with the user's connections
        # who are also interested.
        context = {
            'interested_friends': interested_friends,
            'total_num_interested': total_num_interested,
            'num_interested_friends': num_interested_friends,
        }
        serializer = SavedEventSerializer(serializer.instance, context=context)

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
        saved_events.sort(lambda a, b: 1 if a.created_at > b.created_at else -1)

        # Get the users who are interested in each event.
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

        # Get the number of the user's friends who are interested in each event.
        num_interested_friends = {
            saved_event.event_id: saved_events_qs.filter(
                    event_id=saved_event.event_id) \
                    .exclude(user_id=request.user.id) \
                    .count()
            for saved_event in saved_events
        }

        context = {
            'interested_friends': interested_friends,
            'total_num_interested': total_num_interested,
            'num_interested_friends': num_interested_friends,
        }
        serializer = SavedEventSerializer(data=saved_events, many=True,
                                          context=context)
        serializer.is_valid()
        return Response(serializer.data)
