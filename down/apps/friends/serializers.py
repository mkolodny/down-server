from __future__ import unicode_literals
from rest_framework import serializers
from down.apps.utils.serializers import UnixEpochDateField
from .models import Friendship


class FriendshipSerializer(serializers.ModelSerializer):
    since = UnixEpochDateField(read_only=True)
    updated_at = UnixEpochDateField(read_only=True)

    class Meta:
        model = Friendship


class FriendSerializer(serializers.Serializer):
    friend = serializers.IntegerField()
