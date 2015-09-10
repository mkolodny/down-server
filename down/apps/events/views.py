from __future__ import unicode_literals
import json
from django.conf import settings
from django.db.models import Q
from django.views.generic.base import TemplateView
from hashids import Hashids
from rest_framework import authentication, mixins, status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.exceptions import ValidationError
from rest_framework.filters import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from down.apps.auth.models import User, UserPhone
from down.apps.notifications.utils import send_message
from .filters import EventFilter
from .models import Event, Invitation, LinkInvitation
from .permissions import (
    InviterWasInvited,
    IsAuthenticatedOrReadOnly,
    IsCreator,
    LinkInviterWasInvited,
    WasInvited,
)
from .serializers import (
    EventSerializer,
    InvitationSerializer,
    EventInvitationSerializer,
    LinkInvitationFkObjectsSerializer,
    LinkInvitationSerializer,
    MessageSentSerializer,
)


class EventViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin,
                   mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsCreator, WasInvited)
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def create(self, request, *args, **kwargs):
        # Set the event creator to be the current user.
        request.data['creator'] = request.user.id

        return super(EventViewSet, self).create(request, *args, **kwargs)

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

            # Send push notifications.
            responses = [Invitation.ACCEPTED, Invitation.MAYBE]
            invitations = Invitation.objects.filter(event=event,
                                                    response__in=responses) \
                    .exclude(to_user=request.user) \
                    .exclude(muted=True)
            member_ids = [invitation.to_user_id for invitation in invitations]
            if len(event.title) > 25:
                activity = event.title[:25] + '...'
            else:
                activity = event.title
            message = '{name} to {activity}: {text}'.format(
                    name=request.user.name, activity=activity,
                    text=serializer.data['text'])
            send_message(member_ids, message, sms=False)

            # Update the datetime the event was modified.
            event.save()

            return Response(status=status.HTTP_201_CREATED)
        else:
            # TODO: Test for when the data is invalid.
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['get'], url_path='member-invitations')
    def member_invitations(self, request, pk=None):
        responses = [Invitation.ACCEPTED, Invitation.MAYBE]
        invitations = Invitation.objects.filter(event_id=pk, response__in=responses)
        invitations.select_related('to_user')
        serializer = EventInvitationSerializer(invitations, many=True)
        return Response(serializer.data)

    @detail_route(methods=['get'], url_path='invited-ids')
    def invited_ids(self, request, pk=None):
        invited_ids = Invitation.objects.filter(event_id=pk) \
                .values_list('to_user', flat=True)
        return Response(list(invited_ids))


class InvitationViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin,
                        viewsets.GenericViewSet):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsAuthenticated, InviterWasInvited)
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer

    def get_serializer(self, *args, **kwargs):
        data = kwargs.get('data')
        if data is not None and 'invitations' in data:
            invitations = data['invitations']
            event_id = data['event']
            for invitation in invitations:
                invitation['event'] = event_id
                invitation['from_user'] = self.request.user.id
                invitation['response'] = Invitation.NO_RESPONSE # TODO: test
            kwargs['data'] = invitations
            kwargs['many'] = True

        return super(InvitationViewSet, self).get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        data = request.data
        if type(data) is dict:
            # Make the current user the inviter.
            data['from_user'] = request.user.id

        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            status_code = status.HTTP_201_CREATED
        except ValidationError as error:
            try:
                event_id = request.data.get('event')
                to_user_id = request.data.get('to_user')
                invitation = Invitation.objects.get(event_id=event_id,
                                                    to_user_id=to_user_id)
                serializer = self.get_serializer(invitation)
                status_code = status.HTTP_200_OK
            except Invitation.DoesNotExist:
                # TODO: Test this
                raise error
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status_code, headers=headers)


class LinkInvitationViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin,
                            viewsets.GenericViewSet):
    authentication_classes = (authentication.TokenAuthentication,)
    lookup_field = 'link_id'
    lookup_value_regex = '[a-zA-Z0-9]{6,}'
    permission_classes = (IsAuthenticatedOrReadOnly, LinkInviterWasInvited)
    queryset = LinkInvitation.objects.all()
    serializer_class = LinkInvitationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=False):
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)
        else:
            # TODO: Handle when the error is something other than the link
            # invitation not being unique.
            hashids = Hashids(salt=settings.HASHIDS_SALT, min_length=6)
            data = serializer.data
            link_id = hashids.encode(data['event'], data['from_user'])
            link_invitation = LinkInvitation.objects.get(link_id=link_id)
            serializer = self.get_serializer(link_invitation)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.is_authenticated():
            context = {'to_user': request.user}
        else:
            context = {}
        serializer = LinkInvitationFkObjectsSerializer(instance, context=context)
        return Response(serializer.data)


class SuggestedEventsView(TemplateView):
    template_name = 'suggested-events.html'
