from __future__ import unicode_literals
from rest_framework import serializers
from rest_framework.renderers import JSONRenderer
from rest_framework_gis.serializers import GeoModelSerializer
from .models import Event, Invitation, Place
from down.apps.auth.models import User
from down.apps.auth.serializers import UserSerializer
from down.apps.utils.serializers import (
    PkOnlyPrimaryKeyRelatedField,
    UnixEpochDateField,
)


class InvitationListSerializer(serializers.ListSerializer):

    def create(self, validated_data):
        # Save the new invitations.
        invitations = [Invitation(**obj) for obj in validated_data]
        Invitation.objects.bulk_create(invitations)
        to_user_ids = [invitation.to_user_id for invitation in invitations]
        event_id = invitations[0].event_id
        invitations = Invitation.objects.filter(event_id=event_id,
                                                to_user_id__in=to_user_ids)
        invitations.send()
        return invitations

    def run_validation(self, data=None):
        """
        We override the default `run_validation`, because the validation
        performed by validators and the `.validate()` method should
        be coerced into an error dictionary with a 'non_fields_error' key.
        """
        (is_empty_value, data) = self.validate_empty_values(data)
        if is_empty_value:
            return data

        value = self.to_internal_value(data)
        self.run_validators(value)
        value = self.validate(value)
        assert value is not None, '.validate() should return the validated data'

        return value


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
