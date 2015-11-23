from __future__ import unicode_literals
from django.conf import settings
import requests
from rest_framework import serializers
from rest_framework_gis.serializers import GeoModelSerializer
from rallytap.apps.auth.serializers import FriendSerializer
from rallytap.apps.utils.exceptions import ServiceUnavailable
from rallytap.apps.utils.utils import add_members
from .models import Event, Place, RecommendedEvent, SavedEvent


class PlaceSerializer(GeoModelSerializer):

    class Meta:
        model = Place


class EventSerializer(serializers.ModelSerializer):
    place = PlaceSerializer(required=False)

    class Meta:
        model = Event
        read_only_fields = ('created_at', 'updated_at')

    def create(self, validated_data):
        """
        First we create the place. Then we create an event that's related to the
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

        # Add the creator to the meteor server members list.
        """
        try:
            add_members(event.id, [event.creator_id])
        except requests.exceptions.HTTPError:
            raise ServiceUnavailable()
        """

        return event


class RecommendedEventSerializer(serializers.ModelSerializer):

    class Meta:
        model = RecommendedEvent


class SavedEventSerializer(GeoModelSerializer):
    interested_friends = serializers.SerializerMethodField()
    total_num_interested = serializers.SerializerMethodField()

    class Meta:
        model = SavedEvent
        write_only_fields = ('location',)

    def get_interested_friends(self, obj):
        interested_friends = self.context.get('interested_friends')
        if interested_friends is None:
            return None
        serializer = FriendSerializer(interested_friends, many=True)
        return serializer.data

    def get_total_num_interested(self, obj):
        interested_counts = self.context.get('interested_counts', {})
        return interested_counts.get(obj.event_id)
