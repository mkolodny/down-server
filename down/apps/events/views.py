from __future__ import unicode_literals
from django.db.models import Q
from django.views.generic.base import TemplateView
from rest_framework import authentication, mixins, status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.filters import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from push_notifications.models import APNSDevice
from down.apps.auth.models import User
from .filters import EventFilter
from .models import AllFriendsInvitation, Event, Invitation
from .permissions import (
    AllFriendsInviterWasInvited,
    InviterWasInvited,
    IsCreator,
    IsInvitationsFromUser,
    OtherUsersNotDown,
    WasInvited,
)
from .serializers import (
    AllFriendsInvitationSerializer,
    EventSerializer,
    InvitationSerializer,
    MessageSentSerializer,
)


class EventViewSet(viewsets.ModelViewSet):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsCreator, WasInvited)
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def destroy(self, request, *args, **kwargs):
        """
        Set the event to canceled.
        """
        event = self.get_object()
        event.canceled = True
        event.save()

        serializer = self.get_serializer(event)
        return Response(serializer.data)

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
            invitations = Invitation.objects.filter(event=event) \
                    .filter(Q(response=Invitation.ACCEPTED)
                            | Q(to_user_messaged=True)) \
                    .exclude(to_user=request.user) \
                    .exclude(muted=True)
            member_ids = [invitation.to_user_id for invitation in invitations]
            devices = APNSDevice.objects.filter(user_id__in=member_ids)
            # TODO: Catch exception if sending the message fails.
            devices.send_message(message)

            # Set a flag on the user's invitation marking that they've posted a
            # message on this event's group chat.
            Invitation.objects.filter(event=event, to_user=request.user) \
                    .update(to_user_messaged=True)

            return Response(status=status.HTTP_201_CREATED)
        else:
            # TODO: Test for when the data is invalid.
            return Response(status=status.HTTP_400_BAD_REQUEST)


class InvitationViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin,
                        viewsets.GenericViewSet):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsInvitationsFromUser, InviterWasInvited,
                          OtherUsersNotDown)
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer

    def get_serializer(self, *args, **kwargs):
        data = kwargs.get('data')
        if 'invitations' in data:
            kwargs['data'] = data['invitations']
            kwargs['many'] = True

        return super(InvitationViewSet, self).get_serializer(*args, **kwargs)


class AllFriendsInvitationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsAuthenticated, AllFriendsInviterWasInvited)
    queryset = AllFriendsInvitation.objects.all()
    serializer_class = AllFriendsInvitationSerializer

    def create(self, request, *args, **kwargs):
        # Set the from_user to the currently logged in user.
        data = request.data
        data['from_user'] = request.user.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)


class SuggestedEventsView(TemplateView):
    template_name = 'suggested-events.html'
