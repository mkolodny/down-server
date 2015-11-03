from __future__ import unicode_literals
from phonenumber_field import phonenumber
from rest_framework import serializers
from rest_framework.serializers import ValidationError
from rest_framework_gis.serializers import GeoModelSerializer
from .models import (
    AuthCode,
    FellowshipApplication,
    LinfootFunnel,
    SocialAccount,
    User,
    UserPhone,
)


class AuthCodeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = AuthCode


class FellowshipApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = FellowshipApplication


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
    friends = serializers.SerializerMethodField(required=False)
    facebook_friends = serializers.SerializerMethodField(required=False)

    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'first_name', 'last_name',
                  'image_url', 'username', 'location', 'friends',
                  'updated_at', 'authtoken', 'facebook_friends')
        read_only_fields = ('updated_at', 'friends', 'facebook_friends')

    def get_authtoken(self, obj):
        return self.context.get('authtoken')

    def get_friends(self, obj):
        friends = self.context.get('friends')
        if friends is not None:
            serializer = FriendSerializer(friends, many=True)
            return serializer.data
        else:
            return None

    def get_facebook_friends(self, obj):
        facebook_friends = self.context.get('facebook_friends')
        if facebook_friends is not None:
            serializer = FriendSerializer(facebook_friends, many=True)
            return serializer.data
        else:
            return None

    def update(self, instance, validated_data):
        if validated_data['username'] == 'rallytap':
            raise ValidationError('Username is taken.')

        return super(UserSerializer, self).update(instance, validated_data)


class UserPhoneSerializer(serializers.ModelSerializer):
    user = FriendSerializer(read_only=True)
    phone = PhoneNumberField()

    class Meta:
        model = UserPhone

    def create(self, validated_data):
        try:
            phone = validated_data['phone']
            userphone = UserPhone.objects.get(phone=phone)
            # TODO: Return a 201 status code.
        except UserPhone.DoesNotExist:
            # Create a new empty user.
            user = User(name=phone)
            user.save()

            # Create a user phone with the new user.
            userphone = UserPhone(user=user, phone=validated_data['phone'])
            userphone.save()

        return userphone


class ContactSerializer(serializers.Serializer):
    phone = PhoneNumberField()
    name = serializers.CharField()


class FacebookSessionSerializer(serializers.Serializer):
    access_token = serializers.CharField()


class MatchSerializer(serializers.Serializer):
    first_user = serializers.IntegerField()
    second_user = serializers.IntegerField()


class FriendSelectSerializer(serializers.Serializer):
    user = serializers.IntegerField()
    friend = serializers.IntegerField()
