from __future__ import unicode_literals
import json
import random
import string
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    UserManager,
)
from django.contrib.gis.db import models
from jsonfield import JSONField
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(null=True, blank=True)
    name = models.TextField(null=True, blank=True)
    # Users who were added from contacts don't have first/last names.
    first_name = models.TextField(null=True, blank=True)
    last_name = models.TextField(null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    username = models.TextField(null=True, blank=True, unique=True)
    # Location can only be null from the time the user logs in to the
    # time that they give us permission to view their location.
    location = models.PointField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    friends = models.ManyToManyField('self', through='friends.Friendship',
                                     symmetrical=False,
                                     related_name='related_friends+')
    bulk_ref = models.TextField(null=True, blank=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    points = models.IntegerField(default=100)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_post_notification = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __unicode__(self):
        return unicode(self.name) or ''

    def get_short_name():
        return self.first_name


def default_auth_code():
    first_digit = random.choice(string.digits[1:])
    last_three = ''.join([random.choice(string.digits) for i in xrange(3)])
    return first_digit + last_three

class AuthCode(models.Model):
    code = models.TextField(default=default_auth_code)
    phone = PhoneNumberField(unique=True)

    def __unicode__(self):
        return unicode(self.phone)


class UserPhone(models.Model):
    user = models.ForeignKey(User)
    phone = PhoneNumberField(unique=True)
    bulk_ref = models.TextField(null=True, blank=True, db_index=True)

    def __unicode__(self):
        return unicode(self.user.name)


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

    class Meta:
        unique_together = ('provider', 'uid')

    def __unicode__(self):
        return unicode(self.user.name)


class Points(object):
    SAVED_EVENT = 1
    SENT_INVITATION = 5


class LinfootFunnel(models.Model):
    phone = PhoneNumberField(unique=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return unicode(self.phone)


class FellowshipApplication(models.Model):
    username = models.TextField()
    school = models.TextField()
