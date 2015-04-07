from __future__ import unicode_literals
from rest_framework import serializers
from rest_framework.serializers import ValidationError
from rest_framework_gis.serializers import GeoModelSerializer
from .models import AuthCode, LinfootFunnel, SocialAccount, User, UserPhoneNumber
from phonenumber_field import phonenumber


class AuthCodeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = AuthCode


class LinfootFunnelSerializer(serializers.ModelSerializer):

    class Meta:
        model = LinfootFunnel


class PhoneNumberField(serializers.Field):

    def to_representation(self, obj):
        return unicode(obj)

    def to_internal_value(self, data):
        phone_number = phonenumber.to_python(data)
        
        if phone_number and not phone_number.is_valid():
            raise ValidationError('Invalid phone number: {}'.format(data))
        return phone_number


class SessionSerializer(serializers.Serializer):
    phone = PhoneNumberField()
    code = serializers.IntegerField()


class SocialAccountLoginSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    provider = serializers.IntegerField(default=SocialAccount.FACEBOOK)


class UserSerializer(GeoModelSerializer):
    firebase_token = serializers.ReadOnlyField(required=False)

    class Meta:
        model = User
        exclude = ('password', 'date_joined', 'last_login')


class PhoneSerializer(serializers.Serializer):
    phones = serializers.ListField(child=PhoneNumberField())


class UserPhoneNumberSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    phone = PhoneNumberField()

    class Meta:
        model = UserPhoneNumber
