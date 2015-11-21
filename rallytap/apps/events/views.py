from __future__ import unicode_literals
from django.conf import settings
from django.views.generic.base import TemplateView
from rest_framework import authentication, mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Event
from .permissions import (
    IsCreator,
)
from .serializers import (
    EventSerializer,
)


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


class SuggestedEventsView(TemplateView):
    template_name = 'suggested-events.html'
