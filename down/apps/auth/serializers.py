from __future__ import unicode_literals
from rest_framework import serializers
from .models import SocialAccount, User


class UserSerializer(serializers.ModelSerializer):
    firebase_token = serializers.ReadOnlyField(required=False)

    class Meta:
        model = User
        exclude = ('password', 'date_joined', 'last_login')


class SocialAccountLoginSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    provider = serializers.IntegerField(default=SocialAccount.FACEBOOK)
