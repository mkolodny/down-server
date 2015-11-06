from __future__ import unicode_literals
from django.conf import settings
from django.db.models import Q
import requests
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.renderers import JSONRenderer
from rest_framework_gis.serializers import GeoModelSerializer
from twilio.rest import TwilioRestClient
from .models import Event, Invitation, LinkInvitation, Place
from rallytap.apps.auth.models import User, UserPhone
from rallytap.apps.auth.serializers import FriendSerializer
from rallytap.apps.friends.models import Friendship
from rallytap.apps.notifications.utils import send_message
from rallytap.apps.utils.exceptions import ServiceUnavailable
from rallytap.apps.utils.serializers import (
    PkOnlyPrimaryKeyRelatedField,
)
from rallytap.apps.utils.utils import add_members, remove_member


class PlaceSerializer(GeoModelSerializer):

    class Meta:
        model = Place


class CreateEventInvitationSerializer(serializers.ModelSerializer):
    to_user = PkOnlyPrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Invitation
        fields = ('to_user',)


class EventSerializer(serializers.ModelSerializer):
    place = PlaceSerializer(required=False)
    invitations = CreateEventInvitationSerializer(write_only=True, required=False,
                                                  many=True)

    class Meta:
        model = Event
        read_only_fields = ('created_at', 'updated_at')
        exclude = ('members',)

    def create(self, validated_data):
        """
        Django REST Framework doesn't support writable nested fields by default.
        So first we create the place. Then we create an event that's related to the
        place. Finally, we create the invitations sent out along with the event.

        We're doing this to avoid having to make two HTTP requests for something
        super common - saving an event with a place.
        """
        invitations = [Invitation(**invitation)
                       for invitation in validated_data.pop('invitations')]

        has_place = validated_data.has_key('place')
        if has_place:
            place = Place(**validated_data.pop('place'))
            place.save()

        event = Event(**validated_data)
        if has_place:
            event.place = place
        event.save()

        # Add the creator to the meteor server members list.
        try:
            add_members(event.id, [event.creator_id])
        except requests.exceptions.HTTPError:
            raise ServiceUnavailable()

        for invitation in invitations:
            invitation.event = event
            invitation.from_user_id = event.creator_id
            if invitation.to_user_id == event.creator_id:
                invitation.response = Invitation.ACCEPTED
            else:
                invitation.response = Invitation.NO_RESPONSE
        Invitation.objects.bulk_create(invitations)

        # Notify the `to_user`s users that they were invited.
        user_ids = [invitation.to_user_id for invitation in invitations
                    if invitation.to_user_id != event.creator_id]
        from_user = self.context['request'].user
        message = 'from {name}'.format(name=from_user.name)
        send_message(user_ids, message, event_id=event.id, from_user=from_user)

        return event


class InvitationListSerializer(serializers.ListSerializer):

    def create(self, validated_data):
        # Save the new invitations.
        invitations = [Invitation(**obj) for obj in validated_data]

        # Make sure the event exists.
        try:
            if len(invitations) > 0:
                event_id = invitations[0].event_id
                event = Event.objects.get(id=event_id)

                Invitation.objects.bulk_create(invitations)

                # Notify the `to_user`s users that they were invited.
                user_ids = [invitation.to_user_id for invitation in invitations]
                from_user = self.context['request'].user
                message = 'from {name}'.format(name=from_user.name)
                send_message(user_ids, message, event_id=event.id,
                             from_user=from_user)
        except Event.DoesNotExist:
            raise ValidationError('Event doesn\'t exist')

        return invitations


class InvitationSerializer(serializers.ModelSerializer):
    event = PkOnlyPrimaryKeyRelatedField(queryset=Event.objects.all())
    from_user = PkOnlyPrimaryKeyRelatedField(queryset=User.objects.all())
    to_user = PkOnlyPrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Invitation
        list_serializer_class = InvitationListSerializer
        read_only_fields = ('created_at', 'updated_at')

    def update(self, instance, validated_data):
        """
        Update the event whenever we update an invitation from anything other
        than no response.
        """
        invitation = instance
        new_response = validated_data['response']
        user = self.context['request'].user

        # Update the meteor server's event member list.
        try:
            if new_response in [Invitation.ACCEPTED, Invitation.MAYBE]:
                # Add the user to the meteor server members list.
                add_members(invitation.event_id, [user.id])
            elif invitation.response != Invitation.NO_RESPONSE:
                # The user changed their response from accepted or maybe to
                # declined.
                # Remove the user from the meteor server members list.
                remove_member(invitation.event_id, user)
        except requests.exceptions.HTTPError:
            raise ServiceUnavailable()

        if invitation.response != new_response:
            event = Event.objects.get(id=invitation.event_id)

            # Notify people who want to know.
            if new_response == Invitation.ACCEPTED:
                message = '{name} is down for {event}'.format(name=user.name,
                                                              event=event.title)
            elif new_response == Invitation.MAYBE:
                message = '{name} joined the chat: {event}'.format(
                        name=user.name, event=event.title)
            elif new_response == Invitation.DECLINED:
                message = '{name} can\'t make it to {event}'.format(
                        name=user.name, event=event.title)

            member_responses = [Invitation.ACCEPTED, Invitation.MAYBE]
            joining_event = (new_response in member_responses)
            bailing = (invitation.response in member_responses
                       and new_response == Invitation.DECLINED)
            if joining_event or bailing:
                # Notify other members who've added the user as a friend.
                invitations = Invitation.objects.filter(
                        Q(response=Invitation.ACCEPTED) |
                        Q(response=Invitation.MAYBE), event=event) \
                        .exclude(to_user=user) \
                        .exclude(muted=True)
                member_ids = [_invitation.to_user_id for _invitation in invitations]
                added_me = Friendship.objects.filter(friend=user,
                                                     user_id__in=member_ids)
                to_user_ids = [friendship.user_id for friendship in added_me]

                # Always notify the person who sent the invitation... Unless they
                # invited themselves (they created the event).
                if invitation.from_user_id != user.id:
                    to_user_ids.append(invitation.from_user_id)
            elif new_response == Invitation.DECLINED:
                to_user_ids = [invitation.from_user_id]

            send_message(to_user_ids, message, sms=False)

            if (event.min_accepted is not None
                    and invitation.response == Invitation.NO_RESPONSE
                    and new_response == Invitation.ACCEPTED):
                # If we've hit the min # of people needed for the event to happen,
                # clear the min accepted field.
                num_accepted = Invitation.objects.filter(
                        event=event,
                        response=Invitation.ACCEPTED) \
                        .count()
                if num_accepted == event.min_accepted:
                    event.min_accepted = None
                    event.save()

        for attr, value in validated_data.items():
            setattr(invitation, attr, value)
        invitation.save()

        return invitation


class MyInvitationSerializer(serializers.ModelSerializer):
    event = EventSerializer()
    from_user = FriendSerializer()
    to_user = PkOnlyPrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Invitation
        read_only_fields = ('created_at', 'updated_at')


class EventInvitationSerializer(serializers.ModelSerializer):
    event = PkOnlyPrimaryKeyRelatedField(queryset=Event.objects.all())
    from_user = PkOnlyPrimaryKeyRelatedField(queryset=User.objects.all())
    to_user = FriendSerializer()

    class Meta:
        model = Invitation
        read_only_fields = ('created_at', 'updated_at')


class UserInvitationSerializer(serializers.ModelSerializer):
    event = EventSerializer()
    from_user = PkOnlyPrimaryKeyRelatedField(queryset=User.objects.all())
    to_user = PkOnlyPrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Invitation
        read_only_fields = ('created_at', 'updated_at')


class LinkInvitationSerializer(GeoModelSerializer):
    event = PkOnlyPrimaryKeyRelatedField(queryset=Event.objects.all())
    from_user = PkOnlyPrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = LinkInvitation
        read_only_fields = ('invitation', 'link_id', 'created_at')


class LinkInvitationFkObjectsSerializer(GeoModelSerializer):
    event = EventSerializer()
    from_user = FriendSerializer()
    invitation = serializers.SerializerMethodField(required=False)

    class Meta:
        model = LinkInvitation
        read_only_fields = ('link_id', 'created_at')

    def get_invitation(self, obj):
        to_user = self.context.get('to_user')
        if to_user is None:
            return None

        try:
            invitation = Invitation.objects.get(to_user=to_user,
                                                event=obj.event)
        except Invitation.DoesNotExist:
            invitation = Invitation(from_user=obj.from_user, to_user=to_user,
                                    event=obj.event)
            invitation.save()
        serializer = InvitationSerializer(invitation)
        return serializer.data


class MessageSentSerializer(serializers.Serializer):
    text = serializers.CharField()
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())
