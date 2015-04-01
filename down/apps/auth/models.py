from __future__ import unicode_literals
import json
import random
import string
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.gis.db import models
from jsonfield import JSONField
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractBaseUser):
    email = models.EmailField(null=True, blank=True, unique=True)
    name = models.TextField(null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    username = models.TextField(null=True, blank=True, unique=True)
    # Location can only be null from the time the user logs in to the
    # time that they give us permission to view their location.
    location = models.PointField(null=True, blank=True)
    authtoken = models.TextField(null=True, blank=True)
    firebase_token = models.TextField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    friends = models.ManyToManyField('self', through='friends.Friendship',
                                     symmetrical=False,
                                     related_name='related_friends+')
    facebook_friends = models.ManyToManyField('self',  symmetrical=False,
            related_name='related_facebook_friends+')
    friend_requests = models.ManyToManyField('self',
                                         through='friends.FriendRequests',
                                         symmetrical=False,
                                         related_name='related_friend_requests+')

    # Use name for the username field, since `self.username` might not be set.
    USERNAME_FIELD = 'email'


def default_auth_code():
    first_digit = random.choice(string.digits[1:])
    last_three = ''.join([random.choice(string.digits) for i in xrange(3)])
    return first_digit + last_three

class AuthCode(models.Model):
    code = models.TextField(default=default_auth_code)
    phone = PhoneNumberField(unique=True)


class UserPhoneNumber(models.Model):
    user = models.ForeignKey(User)
    phone = PhoneNumberField(unique=True)


class SocialAccount(models.Model):
    user = models.ForeignKey(User)
    FACEBOOK = 1
    PROVIDER_TYPE = (
        (FACEBOOK, 'facebook'),
    )
    provider = models.SmallIntegerField(choices=PROVIDER_TYPE)
    uid = models.TextField(db_index=True)
    profile = JSONField(default=json.dumps({}))
    last_login = models.DateTimeField(auto_now=True)
    date_joined = models.DateTimeField(auto_now_add=True)


class LinfootFunnel(models.Model):
    phone = PhoneNumberField(unique=True)
    date_created = models.DateTimeField(auto_now_add=True)
