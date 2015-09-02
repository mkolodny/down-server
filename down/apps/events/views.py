from __future__ import unicode_literals
import json
from django.conf import settings
from django.db.models import Q
from django.views.generic.base import TemplateView
from hashids import Hashids
from rest_framework import authentication, mixins, status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.filters import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from push_notifications.models import APNSDevice
from twilio.rest import TwilioRestClient
from down.apps.auth.models import User, UserPhone
from .filters import EventFilter
from .models import Event, Invitation, LinkInvitation
from .permissions import (
    InviterWasInvited,
    IsCreator,
    LinkInviterWasInvited,
    WasInvited,
)
from .serializers import (
    EventSerializer,
    InvitationSerializer,
    EventInvitationSerializer,
    LinkInvitationSerializer,
    MessageSentSerializer,
)


class EventViewSet(viewsets.ModelViewSet):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsCreator, WasInvited)
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def create(self, request, *args, **kwargs):
        # Set the event creator to be the current user.
        request.data['creator'] = request.user.id

        return super(EventViewSet, self).create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Set the event to canceled.
        """
        event = self.get_object()
        event.canceled = True
        event.save()

        # Notify people who were down that the event was canceled.
        message = '{name} canceled {activity}'.format(name=event.creator.name,
                                                      activity=event.title)
        responses = [Invitation.ACCEPTED, Invitation.MAYBE]
        invitations = Invitation.objects.filter(event=event) \
                .filter(Q(response__in=responses)) \
                .exclude(to_user=request.user)
        member_ids = [invitation.to_user_id for invitation in invitations]
        devices = APNSDevice.objects.filter(user_id__in=member_ids)
        # TODO: Catch exception if sending the message fails.
        devices.send_message(message, badge=1)

        # Notify all SMS users that the event was canceled.
        device_ids = set(device.user_id for device in devices)
        sms_user_ids = [member_id for member_id in member_ids
                if member_id not in device_ids]
        userphones = UserPhone.objects.filter(user_id__in=sms_user_ids)
        client = TwilioRestClient(settings.TWILIO_ACCOUNT, settings.TWILIO_TOKEN)
        for userphone in userphones:
            phone = unicode(userphone.phone)
            client.messages.create(to=phone, from_=settings.TWILIO_PHONE,
                                   body=message)

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
            responses = [Invitation.ACCEPTED, Invitation.MAYBE]
            invitations = Invitation.objects.filter(event=event,
                                                    response__in=responses) \
                    .exclude(to_user=request.user) \
                    .exclude(muted=True)
            member_ids = [invitation.to_user_id for invitation in invitations]
            devices = APNSDevice.objects.filter(user_id__in=member_ids)
            # TODO: Catch exception if sending the message fails.
            devices.send_message(message)

            # Update the datetime the event was modified.
            event.save()

            return Response(status=status.HTTP_201_CREATED)
        else:
            # TODO: Test for when the data is invalid.
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['get'])
    def invitations(self, request, pk=None):
        responses = [Invitation.ACCEPTED, Invitation.MAYBE, Invitation.DECLINED]
        invitations = Invitation.objects.filter(event_id=pk, response__in=responses)

        # Only users who have responded accepted, or maybe can view other user's
        # invitations.
        if invitations.filter(to_user=request.user).count() < 1:
            return Response(status=status.HTTP_403_FORBIDDEN)

        invitations.select_related('to_user')
        serializer = EventInvitationSerializer(invitations, many=True)
        return Response(serializer.data)

    @detail_route(methods=['get'], url_path='invited-ids')
    def invited_ids(self, request, pk=None):
        invited_ids = Invitation.objects.filter(event_id=pk,
                                                from_user=request.user) \
                .exclude(to_user=request.user) \
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
        if 'invitations' in data:
            invitations = data['invitations']
            event_id = data['event']
            for invitation in invitations:
                invitation['event'] = event_id
                invitation['from_user'] = self.request.user.id
                invitation['response'] = Invitation.NO_RESPONSE # TODO: test
            kwargs['data'] = invitations
            kwargs['many'] = True

        return super(InvitationViewSet, self).get_serializer(*args, **kwargs)


class LinkInvitationViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin,
                            viewsets.GenericViewSet):
    authentication_classes = (authentication.TokenAuthentication,)
    lookup_field = 'link_id'
    lookup_value_regex = '[a-zA-Z0-9]{6,}'
    permission_classes = (IsAuthenticated, LinkInviterWasInvited,)
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


class SuggestedEventsView(TemplateView):
    template_name = 'suggested-events.html'
