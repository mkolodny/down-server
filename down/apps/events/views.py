from __future__ import unicode_literals
from rest_framework import authentication, mixins, status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.filters import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from down.apps.auth.models import User
from .filters import EventFilter
from .models import Event, Invitation
from .permissions import (
    InviterWasInvited,
    IsFromUser,
    OtherUsersNotDown,
    WasInvited,
)
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
            self.check_object_permissions(request, event)

            if len(event.title) > 25:
                activity = event.title[:25] + '...'
            else:
                activity = event.title
            message = '{name} to {activity}: {text}'.format(
                    name=request.user.name, activity=activity,
                    text=serializer.data['text'])
            notify_responses = [Invitation.ACCEPTED, Invitation.NO_RESPONSE]
            devices = event.get_member_devices(request.user, notify_responses)
            # TODO: Catch exception if sending the message fails.
            devices.send_message(message)

            return Response(status=status.HTTP_201_CREATED)
        else:
            # TODO: Test for when the data is invalid.
            return Response(status=status.HTTP_400_BAD_REQUEST)


class InvitationViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin,
                        viewsets.GenericViewSet):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsFromUser, InviterWasInvited,
                          OtherUsersNotDown)
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer

    def get_serializer(self, *args, **kwargs):
        data = kwargs.get('data')
        if 'invitations' in data:
            kwargs['data'] = data['invitations']
            kwargs['many'] = True

        return super(InvitationViewSet, self).get_serializer(*args, **kwargs)
