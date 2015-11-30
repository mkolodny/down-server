from __future__ import unicode_literals
from django.conf import settings
import requests
from rest_framework import serializers
from rest_framework_gis.serializers import GeoModelSerializer
from rallytap.apps.auth.models import User
from rallytap.apps.auth.serializers import FriendSerializer
from rallytap.apps.friends.models import Friendship
from rallytap.apps.notifications.utils import send_message
from rallytap.apps.utils.exceptions import ServiceUnavailable
from rallytap.apps.utils.serializers import PkOnlyPrimaryKeyRelatedField
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

        user = self.context['request'].user
        saved_event = SavedEvent(event=event, user=user, location=user.location)
        saved_event.save()

        # Notify users who have added the user as a friend.
        friend_ids = Friendship.objects.filter(friend=user) \
                .values_list('user_id', flat=True)
        if event.friends_only:
            added_ids = set(Friendship.objects.filter(user=user) \
                    .values_list('friend_id', flat=True))
            friend_ids = [friend_id for friend_id in friend_ids
                    if friend_id in added_ids]
        message = 'Your friend is interested in "{title}".'.format(
                name=user.name, title=event.title)
        send_message(friend_ids, message)

        # Add the creator to the meteor server members list.
        try:
            add_members(event.id, event.creator_id)
        except requests.exceptions.HTTPError:
            raise ServiceUnavailable()

        return event


class RecommendedEventSerializer(serializers.ModelSerializer):

    class Meta:
        model = RecommendedEvent


class SavedEventSerializer(GeoModelSerializer):
    event = PkOnlyPrimaryKeyRelatedField(queryset=Event.objects.all())
    user = PkOnlyPrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = SavedEvent


class SavedEventFullEventSerializer(GeoModelSerializer):
    event = EventSerializer()
    user = PkOnlyPrimaryKeyRelatedField(queryset=User.objects.all())
    interested_friends = serializers.SerializerMethodField()
    total_num_interested = serializers.SerializerMethodField()
    num_interested_friends = serializers.SerializerMethodField()

    class Meta:
        model = SavedEvent
        exclude = ('location',)

    def get_interested_friends(self, obj):
        interested_friends = self.context.get('interested_friends')
        if interested_friends is None:
            return None
        friends = interested_friends.get(obj.event_id)
        serializer = FriendSerializer(friends, many=True)
        return serializer.data

    def get_total_num_interested(self, obj):
        total_num_interested = self.context.get('total_num_interested', {})
        return total_num_interested.get(obj.event_id)

    def get_num_interested_friends(self, obj):
        num_interested_friends = self.context.get('num_interested_friends', {})
        return num_interested_friends.get(obj.event_id)
