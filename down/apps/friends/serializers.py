from __future__ import unicode_literals
from rest_framework import serializers
from .models import Friendship


class FriendshipSerializer(serializers.ModelSerializer):

    class Meta:
        model = Friendship
        read_only_fields = ('since', 'updated_at')


class FriendSerializer(serializers.Serializer):
    friend = serializers.IntegerField()
