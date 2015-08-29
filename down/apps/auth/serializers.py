from __future__ import unicode_literals
from phonenumber_field import phonenumber
from rest_framework import serializers
from rest_framework.serializers import ValidationError
from rest_framework_gis.serializers import GeoModelSerializer
from .models import AuthCode, LinfootFunnel, SocialAccount, User, UserPhone


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


class FriendSerializer(GeoModelSerializer):

    class Meta:
        model = User
        depth = 1
        fields = ('id', 'email', 'name', 'first_name', 'last_name',
                  'image_url', 'username', 'location')


class UserSerializer(GeoModelSerializer):
    authtoken = serializers.SerializerMethodField(required=False)
    friends = FriendSerializer(required=False, many=True)
    facebook_friends = serializers.SerializerMethodField(required=False)

    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'first_name', 'last_name',
                  'image_url', 'username', 'location', 'friends',
                  'updated_at', 'authtoken', 'facebook_friends')
        read_only_fields = ('updated_at', 'friends', 'facebook_friends')

    def get_authtoken(self, obj):
        return self.context.get('authtoken')

    def get_facebook_friends(self, obj):
        facebook_friends = self.context.get('facebook_friends')
        if facebook_friends is not None:
            serializer = FriendSerializer(facebook_friends, many=True)
            return serializer.data
        else:
            return None


class PhoneSerializer(serializers.Serializer):
    phones = serializers.ListField(child=PhoneNumberField())


class UserPhoneSerializer(serializers.ModelSerializer):
    user = FriendSerializer(read_only=True)
    phone = PhoneNumberField()

    class Meta:
        model = UserPhone

    def create(self, validated_data):
        # Create a new empty user.
        user = User()
        user.save()

        # Create a user phone with the new user.
        userphone = UserPhone(user=user, phone=validated_data['phone'])
        userphone.save()

        return userphone


class ContactSerializer(serializers.Serializer):
    phone = PhoneNumberField()
    name = serializers.CharField()
