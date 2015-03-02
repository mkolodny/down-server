from __future__ import unicode_literals
from rest_framework import viewsets
from .models import Event, Invitation
from .serializers import EventSerializer, InvitationSerializer


# TODO: Security
class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    queryset = Event.objects.all()


# TODO: Security
class InvitationViewSet(viewsets.ModelViewSet):
    serializer_class = InvitationSerializer
    queryset = Invitation.objects.all()
