from __future__ import unicode_literals
from rest_framework import serializers
from down.apps.auth.models import User
from down.apps.notifications.utils import send_message
from down.apps.utils.utils import add_members
from .models import Friendship


class FriendshipSerializer(serializers.ModelSerializer):

    class Meta:
        model = Friendship
        read_only_fields = ('since', 'updated_at')

    def create(self, validated_data):
        # Notify the user's new friend that the user added them as a friend.
        user = validated_data['user']
        friend_id = validated_data['friend'].id
        user_ids = [friend_id]

        try:
            # Check if the user's new friend has already added the user as a
            # friend.
            friend_friendship = Friendship.objects.get(user=friend_id,
                                                       friend=user)

            # Create the user's friendship with `was_acknowledged` already set to
            # True.
            data = dict(validated_data, **{'was_acknowledged': True})
            friendship = super(FriendshipSerializer, self).create(data)

            # Send the friend this user added a notification.
            message = '{name} (@{username}) added you back!'.format(
                    name=user.name, username=user.username)
            send_message(user_ids, message)

            # Set the friend's friendship to acknowledged.
            if not friend_friendship.was_acknowledged:
                friend_friendship.was_acknowledged = True
                friend_friendship.save()
        except Friendship.DoesNotExist:
            friendship = super(FriendshipSerializer, self).create(validated_data)

            # Create a group chat for this friendship.
            group_id = '{user_id},{friend_id}'.format(user_id=user.id,
                                                      friend_id=friend_id)
            add_members(group_id, [user.id, friend_id])

            # Send the friend this user added a notification.
            message = '{name} (@{username}) added you as a friend!'.format(
                    name=user.name, username=user.username)
            send_message(user_ids, message, added_friend=True)

        return friendship


class FriendSerializer(serializers.Serializer):
    friend = serializers.IntegerField()
