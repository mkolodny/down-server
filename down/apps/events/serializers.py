from __future__ import unicode_literals
from datetime import datetime
import time
from rest_framework import serializers
import pytz
from .models import Event, Invitation, Place
from down.apps.auth.serializers import UserSerializer


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
    datetime_sent = UnixEpochDateField(read_only=True)

    class Meta:
        model = Invitation


class PlaceSerializer(serializers.ModelSerializer):

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
        """
        place = Place(**validated_data.pop('place'))
        place.save()

        event = Event(**validated_data)
        event.place = place
        event.save()
        return event
