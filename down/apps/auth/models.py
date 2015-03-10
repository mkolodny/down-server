from __future__ import unicode_literals
import json
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.gis.db import models
from jsonfield import JSONField


class User(AbstractBaseUser):
    email = models.EmailField(unique=True)
    name = models.TextField()
    image_url = models.URLField()
    username = models.TextField(null=True, unique=True)
    # Location can only be null from the time the user logs in to the
    # time that they give us permission to view their location.
    location = models.PointField(null=True, blank=True)
    firebase_token = models.TextField(null=True, unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    friends = models.ManyToManyField('self', through='friends.Friendship',
                                     symmetrical=False,
                                     related_name='related_friends+')
    friend_requests = models.ManyToManyField('self',
                                         through='friends.FriendRequests',
                                         symmetrical=False,
                                         related_name='related_friend_requests+')

    # Use name for the username field, since `self.username` might not be set.
    USERNAME_FIELD = 'email'


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
