from __future__ import unicode_literals
from datetime import datetime
import time
from rest_framework import serializers
from rest_framework_gis.serializers import GeoModelSerializer
import pytz
from down.apps.auth.models import User
from down.apps.auth.serializers import UserSerializer
from .models import Event, Invitation, Place


# TODO: Move this somewhere more general.
class UnixEpochDateField(serializers.DateTimeField):

    def to_representation(self, value):
        """
        Return epoch time for a datetime object or ``None``.
        """
        try:
            return int(time.mktime(value.timetuple()))
        except (AttributeError, TypeError):
            return None

    def to_internal_value(self, value):
        return datetime.utcfromtimestamp(int(value)).replace(tzinfo=pytz.utc)


class InvitationSerializer(serializers.ModelSerializer):
    created_at = UnixEpochDateField(read_only=True)

    class Meta:
        model = Invitation


class PlaceSerializer(GeoModelSerializer):

    class Meta:
        model = Place


class EventSerializer(serializers.ModelSerializer):
    created_at = UnixEpochDateField(read_only=True)
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
