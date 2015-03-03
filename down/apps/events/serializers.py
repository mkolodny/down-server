from __future__ import unicode_literals
from rest_framework import serializers
from .models import Event, Invitation, Place
from down.apps.auth.serializers import UserSerializer


class InvitationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Invitation


class PlaceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Place


class EventSerializer(serializers.ModelSerializer):
    place = PlaceSerializer()

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
