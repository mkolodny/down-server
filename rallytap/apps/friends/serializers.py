from __future__ import unicode_literals
from rest_framework import serializers
from rallytap.apps.auth.models import User
from rallytap.apps.notifications.utils import send_message
from rallytap.apps.utils.utils import add_members
from .models import Friendship


class FriendshipSerializer(serializers.ModelSerializer):

    class Meta:
        model = Friendship
        read_only_fields = ('since', 'updated_at')

    def create(self, validated_data):
        friendship = super(FriendshipSerializer, self).create(validated_data)

        # Notify the user's new friend that the user added them as a friend.
        user = self.context['request'].user
        friend_id = validated_data['friend'].id
        user_ids = [friend_id]

        try:
            # Check if the user's new friend has already added the user as a
            # friend.
            Friendship.objects.get(user=friend_id, friend=user)

            # Send the friend this user added a notification.
            message = '{name} (@{username}) added you back!'.format(
                    name=user.name, username=user.username)
            send_message(user_ids, message)
        except Friendship.DoesNotExist:
            # Send the friend this user added a notification.
            message = '{name} (@{username}) added you as a friend!'.format(
                    name=user.name, username=user.username)
            send_message(user_ids, message, added_friend=True)

        return friendship


class FriendSerializer(serializers.Serializer):
    friend = serializers.IntegerField()


class MessageSerializer(serializers.Serializer):
    text = serializers.CharField()
    to_user = serializers.IntegerField()
