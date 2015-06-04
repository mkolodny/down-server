from __future__ import unicode_literals
from django.conf import settings
from push_notifications.models import APNSDevice
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.renderers import JSONRenderer
from rest_framework_gis.serializers import GeoModelSerializer
from twilio.rest import TwilioRestClient
from .models import AllFriendsInvitation, Event, Invitation, Place
from down.apps.auth.models import User, UserPhone
from down.apps.auth.serializers import UserSerializer
from down.apps.events.models import get_event_date
from down.apps.utils.serializers import (
    PkOnlyPrimaryKeyRelatedField,
    UnixEpochDateField,
)


class InvitationListSerializer(serializers.ListSerializer):

    def create(self, validated_data):
        # Save the new invitations.
        invitations = [Invitation(**obj) for obj in validated_data]

        # Make sure all of the events we're creating invitations for are the
        # same.
        event_id = invitations[0].event.id
        if not all((invitation.event.id == event_id) for invitation in invitations):
            raise ValidationError('Not all events are the same')

        # Make sure all of the from_users are the same.
        from_user_id = invitations[0].from_user.id
        if not all((invitation.from_user.id == from_user_id)
                   for invitation in invitations):
            raise ValidationError('Not all `from_user` are the same')

        # Make sure the event exists.
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            raise ValidationError('Event doesn\'t exist')

        Invitation.objects.bulk_create(invitations)
        to_user_ids = [invitation.to_user_id for invitation in invitations]
        invitations = Invitation.objects.filter(event=event,
                                                to_user_id__in=to_user_ids)
        invitations.send()
        return invitations


class InvitationSerializer(serializers.ModelSerializer):
    event = PkOnlyPrimaryKeyRelatedField(queryset=Event.objects.all())
    from_user = PkOnlyPrimaryKeyRelatedField(queryset=User.objects.all())
    to_user = PkOnlyPrimaryKeyRelatedField(queryset=User.objects.all())
    created_at = UnixEpochDateField(read_only=True)
    updated_at = UnixEpochDateField(read_only=True)

    class Meta:
        model = Invitation
        list_serializer_class = InvitationListSerializer


class PlaceSerializer(GeoModelSerializer):

    class Meta:
        model = Place


class AllFriendsInvitationSerializer(GeoModelSerializer):

    class Meta:
        model = AllFriendsInvitation


class EventSerializer(serializers.ModelSerializer):
    created_at = UnixEpochDateField(read_only=True)
    updated_at = UnixEpochDateField(read_only=True)
    members = InvitationSerializer(source='invitation_set', many=True,
                                   read_only=True)
    place = PlaceSerializer(required=False)
    datetime = UnixEpochDateField(required=False)

    class Meta:
        model = Event

    def create(self, validated_data):
        """
        Django REST Framework doesn't support writable nested fields by default.
        So first we create the place. Then we create an event that's related to the
        place.

        We're doing this to avoid having to make two HTTP requests for something
        super common - saving an event with a place.
        """
        has_place = validated_data.has_key('place')
        if has_place:
            place = Place(**validated_data.pop('place'))
            place.save()

        event = Event(**validated_data)
        if has_place:
            event.place = place
        event.save()
        return event

    def update(self, instance, validated_data):
        """
        Django REST Framework doesn't support writable nested fields by default.
        So first we create the place. Then we update the event.

        We're doing this to avoid having to make two HTTP requests for something
        super common - saving an event with a place.
        """
        has_place = validated_data.has_key('place')
        has_datetime = validated_data.has_key('datetime')

        if has_place:
            place = Place(**validated_data.pop('place'))
            place.save()

        event = instance

        # Check whether the place, date, or both were updated.
        place_edited = (has_place and place.name != event.place.name)
        place_removed = (not has_place and event.place_id is not None)
        datetime_edited = (has_datetime
                and validated_data['datetime'] != event.datetime)
        datetime_removed = (not has_datetime and event.datetime != None)

        for attr, value in validated_data.items():
            setattr(event, attr, value)
        if has_place:
            event.place = place
        # Since we can't send back a null value from the client right now, we
        # have to explictly set missing fields to None.
        else:
            event.place = None
        if not validated_data.has_key('datetime'):
            event.datetime = None
        event.save()

        # Notify people who haven't declined their invitation to this event that
        # the place/datetime were updated.
        creator = event.creator

        # Get devices we should send push notifications to.
        responses = [Invitation.NO_RESPONSE, Invitation.ACCEPTED]
        invites = Invitation.objects.filter(event=event, response__in=responses) \
                .exclude(to_user=creator)
        member_ids = [invite.to_user_id for invite in invites]
        devices = APNSDevice.objects.filter(user_id__in=member_ids)

        # Get phones we should text the update to.
        device_user_ids = [device.user_id for device in devices]
        deviceless_invites = invites.exclude(to_user_id__in=device_user_ids)
        deviceless_user_ids = [invite.to_user_id for invite in deviceless_invites]
        userphones = UserPhone.objects.filter(user_id__in=deviceless_user_ids)
        phones = [unicode(userphone.phone) for userphone in userphones]

        client = TwilioRestClient(settings.TWILIO_ACCOUNT, settings.TWILIO_TOKEN)
        signature = '\n--\nSent from Down (http://down.life/app)'

        if datetime_edited and has_place:
            date = get_event_date(event, place.geo)
        elif datetime_edited:
            date = get_event_date(event, creator.location)

        if place_edited and datetime_edited:
            notif = ('{name} changed the location and time where {activity} is'
                     ' happening.').format(name=creator.name,
                                           activity=event.title)
            sms_extra = (' The new location is {place}, and the new time is'
                         ' {date}.').format(place=place.name, date=date)
        elif place_edited and not datetime_removed:
            notif = ('{name} changed the location where {activity} is'
                     ' happening.').format(name=creator.name, activity=event.title,)
            sms_extra = ' The new location is {place}.'.format(place=place.name)
        elif place_edited and datetime_removed:
            notif = ('{name} changed the location where {activity} is'
                     ' happening.').format(name=creator.name, activity=event.title)
            sms_extra = (' The new location is {place}. The time was'
                         ' removed').format(place=place.name)
        elif datetime_edited and not place_removed:
            notif = ('{name} changed the time when {activity} is'
                     ' happening.').format(name=creator.name, activity=event.title)
            sms_extra = ' The new time is {date}.'.format(date=date)
        elif datetime_edited and place_removed:
            notif = ('{name} changed the location and time where {activity} is'
                     ' happening.').format(name=creator.name, activity=event.title)
            sms_extra = (' The location was removed. The new time is'
                    ' {date}.').format(date=date)
        elif place_removed and not datetime_removed:
            notif = ('{name} removed the location where {activity} is'
                     ' happening.').format(name=creator.name, activity=event.title)
            sms_extra = ''
        elif datetime_removed and not place_removed:
            notif = ('{name} removed the time when {activity} is'
                     ' happening.').format(name=creator.name, activity=event.title)
            sms_extra = ''
        elif place_removed and datetime_removed:
            notif = ('{name} removed the location and time where {activity} is'
                     ' happening.').format(name=creator.name, activity=event.title)
            sms_extra = ''

        devices.send_message(notif, badge=1)
        sms = notif + sms_extra + signature
        for phone in phones:
            client.messages.create(to=phone, from_=settings.TWILIO_PHONE, body=sms)
        
        return event


class MessageSentSerializer(serializers.Serializer):
    text = serializers.CharField()
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())
