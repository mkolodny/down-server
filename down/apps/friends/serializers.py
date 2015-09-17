from __future__ import unicode_literals
from rest_framework import serializers
from down.apps.notifications.utils import send_message
from .models import Friendship


class FriendshipSerializer(serializers.ModelSerializer):

    class Meta:
        model = Friendship
        read_only_fields = ('since', 'updated_at')

    def create(self, validated_data):
        friendship = super(FriendshipSerializer, self).create(validated_data)

        # Notify the user's new friend that the user added them as a friend.
        user = friendship.user
        user_ids = [friendship.friend_id]
        # Check if the user's new friend has already added the user as a friend.
        if Friendship.objects.filter(user=friendship.friend_id, friend=user):
            message = '{name} (@{username}) added you back!'.format(
                    name=user.name, username=user.username)
            send_message(user_ids, message)
        else:
            message = '{name} (@{username}) added you as a friend!'.format(
                    name=user.name, username=user.username)
            send_message(user_ids, message, added_friend=True)

        return friendship


class FriendSerializer(serializers.Serializer):
    friend = serializers.IntegerField()
