from __future__ import unicode_literals
from django.conf import settings
from django.views.generic.base import TemplateView
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
from rallytap.apps.friends.models import Friendship


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


class SavedEventViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
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

        # See how many users are interested in this event. Convert the queryset
        # to a list so that it's only evaluated once.
        event_id = serializer.data['event']
        saved_events = list(SavedEvent.objects.filter(event_id=event_id))
        total_num_interested = len(saved_events)
        interested_counts = {event_id: total_num_interested}

        # See which of the user's friends are interested in this event.
        friends_dict = {
            friendship.friend.id: friendship.friend
            for friendship in Friendship.objects.filter(user=request.user)
        }
        interested_friends = [friends_dict[saved_event.user_id]
                for saved_event in saved_events
                if friends_dict.has_key(saved_event.user_id)]
        # Since creating the saved event removes any context from the serializer,
        # we have to serialize the saved event again with the user's connections
        # who are also interested.
        context = {
            'interested_friends': interested_friends,
            'interested_counts': interested_counts,
        }
        serializer = SavedEventSerializer(serializer.instance, context=context)

        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)
