from __future__ import unicode_literals
from rest_framework import serializers
from rest_framework.renderers import JSONRenderer
from rest_framework.serializers import PrimaryKeyRelatedField
from rest_framework_gis.serializers import GeoModelSerializer
from down.apps.auth.models import User
from down.apps.auth.serializers import UserSerializer
from down.apps.utils.serializers import UnixEpochDateField
from .models import Event, Invitation, Place


class InvitationListSerializer(serializers.ListSerializer):

    def create(self, validated_data):
        #print validated_data[0]['event'].title
        # Save the new invitations.
        invitations = [Invitation(**obj) for obj in validated_data]
        Invitation.objects.bulk_create(invitations)
        to_user_ids = [invitation.to_user_id for invitation in invitations]
        event_id = invitations[0].event_id
        invitations = Invitation.objects.filter(event_id=event_id,
                                                to_user_id__in=to_user_ids)
        invitations.send()
        return invitations


class InvitationSerializer(serializers.ModelSerializer):
    created_at = UnixEpochDateField(read_only=True)
    updated_at = UnixEpochDateField(read_only=True)

    class Meta:
        model = Invitation
        list_serializer_class = InvitationListSerializer


class PlaceSerializer(GeoModelSerializer):

    class Meta:
        model = Place


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
        # TODO: Test when the event doesn't have a place.
        event_has_place = validated_data.has_key('place')
        if event_has_place:
            place = Place(**validated_data.pop('place'))
            place.save()

        event = Event(**validated_data)
        if event_has_place:
            event.place = place
        event.save()
        return event


class MessageSentSerializer(serializers.Serializer):
    text = serializers.CharField()
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())
