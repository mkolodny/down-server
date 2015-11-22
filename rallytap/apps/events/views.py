from __future__ import unicode_literals
from django.conf import settings
from django.views.generic.base import TemplateView
from rest_framework import authentication, mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from .filters import NearbyPlaceFilter
from .models import Event, RecommendedEvent
from .permissions import IsCreator
from .serializers import EventSerializer, RecommendedEventSerializer


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
