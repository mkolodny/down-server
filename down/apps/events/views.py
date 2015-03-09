from __future__ import unicode_literals
from rest_framework import status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from .models import Event, Invitation
from .serializers import EventSerializer, InvitationSerializer


# TODO: Security
class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    queryset = Event.objects.all()

    @detail_route(methods=['post'])
    def messages(self, request, pk=None):
        # Notify the user's who are down for the event (except for the user that
        # posted the message) about a new message.
        return Response(status=status.HTTP_201_CREATED)



# TODO: Security
class InvitationViewSet(viewsets.ModelViewSet):
    serializer_class = InvitationSerializer
    queryset = Invitation.objects.all()
