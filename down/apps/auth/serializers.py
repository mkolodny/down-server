from __future__ import unicode_literals
from rest_framework import serializers
from rest_framework_gis.serializers import GeoModelSerializer
from .models import LinfootFunnel, SocialAccount, User


class UserSerializer(GeoModelSerializer):
    firebase_token = serializers.ReadOnlyField(required=False)

    class Meta:
        model = User
        exclude = ('password', 'date_joined', 'last_login')


class SocialAccountLoginSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    provider = serializers.IntegerField(default=SocialAccount.FACEBOOK)


class LinfootFunnelSerializer(serializers.ModelSerializer):

    class Meta:
        model = LinfootFunnel
