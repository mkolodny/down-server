from __future__ import unicode_literals
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from down.apps.auth.models import User
from .models import Event, Invitation
from .serializers import (
    EventSerializer,
    InvitationSerializer,
    MessageSentSerializer,
)


# TODO: Security
class EventViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin,
                   mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = EventSerializer
    queryset = Event.objects.all()

    @detail_route(methods=['post'])
    def messages(self, request, pk=None):
        """
        Notify the users who are down for the event (except for the user that
        posted the message) about a new message.
        """
        data = {
            'text': request.data.get('text'),
            'user': request.data.get('user'),
            'event': pk,
        }
        serializer = MessageSentSerializer(data=data)
        if serializer.is_valid():
            # Notify the other users who are down for the event about the user's
            # message.
            user = User.objects.get(id=serializer.data['user'])
            event = Event.objects.get(id=serializer.data['event'])

            if len(event.title) > 25:
                activity = event.title[:25] + '...'
            else:
                activity = event.title
            message = '{name} to {activity}: {text}'.format(
                    name=user.name, activity=activity,
                    text=serializer.data['text'])
            devices = event.get_relevant_member_devices(user)
            # TODO: Catch exception if sending the message fails.
            devices.send_message(message)

            return Response(status=status.HTTP_201_CREATED)
        else:
            print serializer.errors
            # TODO: Test for when the data is invalid.
            return Response(status=status.HTTP_400_BAD_REQUEST)


# TODO: Security
class InvitationViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin,
                        mixins.ListModelMixin, mixins.UpdateModelMixin,
                        viewsets.GenericViewSet):
    serializer_class = InvitationSerializer
    queryset = Invitation.objects.all()
