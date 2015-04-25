from __future__ import unicode_literals
from phonenumber_field import phonenumber
from rest_framework import serializers
from rest_framework.serializers import ValidationError
from rest_framework_gis.serializers import GeoModelSerializer
from down.apps.utils.serializers import UnixEpochDateField
from .models import AuthCode, LinfootFunnel, SocialAccount, User, UserPhoneNumber


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


class SocialAccountSyncSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    provider = serializers.IntegerField(default=SocialAccount.FACEBOOK)


class UserSerializer(GeoModelSerializer):
    authtoken = serializers.ReadOnlyField(required=False)
    firebase_token = serializers.ReadOnlyField(required=False)
    updated_at = UnixEpochDateField(read_only=True)

    class Meta:
        model = User
        exclude = ('password', 'date_joined', 'last_login')


class PhoneSerializer(serializers.Serializer):
    phones = serializers.ListField(child=PhoneNumberField())


class UserPhoneNumberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    phone = PhoneNumberField()

    class Meta:
        model = UserPhoneNumber

    def create(self, validated_data):
        # Create a new empty user.
        user = User()
        user.save()

        # Create a user phone with the new user.
        userphone = UserPhoneNumber(user=user, phone=validated_data['phone'])
        userphone.save()

        return userphone
