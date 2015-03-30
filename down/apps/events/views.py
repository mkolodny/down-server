from __future__ import unicode_literals
from rest_framework import authentication, mixins, status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from down.apps.auth.models import User
from .models import Event, Invitation
from .permissions import WasInvited, IsEventCreatorOrUpdateOnly
from .serializers import (
    EventSerializer,
    InvitationSerializer,
    MessageSentSerializer,
)


class EventViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin,
                   mixins.CreateModelMixin, viewsets.GenericViewSet):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsAuthenticated, WasInvited)
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    @detail_route(methods=['post'])
    def messages(self, request, pk=None):
        """
        Notify the users who are down for the event (except for the user that
        posted the message) about a new message.
        """
        data = {
            'text': request.data.get('text'),
            'event': pk,
        }
        serializer = MessageSentSerializer(data=data)
        if serializer.is_valid():
            # Notify the other users who are down for the event about the user's
            # message.
            event = Event.objects.get(id=serializer.data['event'])

            # Make sure that the current user was invited to the event.
            # TODO: Figure out how to use rest framework's permission classes for
            # this.
            try:
                Invitation.objects.get(event=event, to_user=request.user)
            except Invitation.DoesNotExist:
                return Response(status=status.HTTP_403_FORBIDDEN)

            if len(event.title) > 25:
                activity = event.title[:25] + '...'
            else:
                activity = event.title
            message = '{name} to {activity}: {text}'.format(
                    name=request.user.name, activity=activity,
                    text=serializer.data['text'])
            devices = event.get_relevant_member_devices(request.user)
            # TODO: Catch exception if sending the message fails.
            devices.send_message(message)

            return Response(status=status.HTTP_201_CREATED)
        else:
            # TODO: Test for when the data is invalid.
            return Response(status=status.HTTP_400_BAD_REQUEST)


class InvitationViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin,
                        viewsets.GenericViewSet):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsEventCreatorOrUpdateOnly)
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
