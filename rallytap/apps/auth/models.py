from __future__ import unicode_literals
import json
import random
import string
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.gis.db import models
from jsonfield import JSONField
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractBaseUser):
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

    USERNAME_FIELD = 'username'

    def __unicode__(self):
        return unicode(self.name) or ''


def default_auth_code():
    first_digit = random.choice(string.digits[1:])
    last_three = ''.join([random.choice(string.digits) for i in xrange(3)])
    return first_digit + last_three

class AuthCode(models.Model):
    code = models.TextField(default=default_auth_code)
    phone = PhoneNumberField(unique=True)


class UserPhone(models.Model):
    user = models.ForeignKey(User)
    phone = PhoneNumberField(unique=True)
    bulk_ref = models.TextField(null=True, blank=True, db_index=True)


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


class Group(models.Model):
    name = models.TextField()
    domain = models.TextField(unique=True)


class UserGroup(models.Model):
    user = models.ForeignKey(User)
    group = models.ForeignKey(Group)

    class Meta:
        unique_together = ('user', 'group')


class Points(object):
    ACCEPTED_INVITATION = 5
    IGNORED_INVITATION = -5
    SENT_INVITATION = 1
    SELECTED_FRIEND = 1


class LinfootFunnel(models.Model):
    phone = PhoneNumberField(unique=True)
    date_created = models.DateTimeField(auto_now_add=True)


class FellowshipApplication(models.Model):
    username = models.TextField()
    school = models.TextField()
