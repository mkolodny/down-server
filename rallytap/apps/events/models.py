from __future__ import unicode_literals
from datetime import timedelta
import json
import re
from django.contrib.gis.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from hashids import Hashids
import pytz
import requests
from twilio.rest import TwilioRestClient
from rallytap.apps.auth.models import User, UserPhone
from rallytap.apps.friends.models import Friendship


class Place(models.Model):
    name = models.TextField()
    geo = models.PointField(null=True, blank=True)


class Event(models.Model):
    title = models.TextField()
    creator = models.ForeignKey(User, related_name='creators')
    canceled = models.BooleanField(default=False)
    # Set to true once an event chat has been deleted on the meteor server.
    expired = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    datetime = models.DateTimeField(null=True, blank=True)
    place = models.ForeignKey(Place, null=True, blank=True)
    members = models.ManyToManyField(User, through='Invitation',
                                     through_fields=('event', 'to_user'))


class Invitation(models.Model):
    from_user = models.ForeignKey(User, related_name='related_from_user+')
    to_user = models.ForeignKey(User, related_name='related_to_user+')
    event = models.ForeignKey(Event)
    NO_RESPONSE = 0
    ACCEPTED = 1
    DECLINED = 2
    MAYBE = 3
    RESPONSE_CHOICES = (
        (NO_RESPONSE, 'no response'),
        (ACCEPTED, 'accepted'),
        (DECLINED, 'declined'),
        (MAYBE, 'maybe'),
    )
    response = models.SmallIntegerField(choices=RESPONSE_CHOICES,
                                        default=NO_RESPONSE)
    muted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('to_user', 'event')


class LinkInvitation(models.Model):
    event = models.ForeignKey(Event)
    from_user = models.ForeignKey(User)
    link_id = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'from_user')

    def save(self, *args, **kwargs):
        if not self.link_id:
            hashids = Hashids(salt=settings.HASHIDS_SALT, min_length=6)
            self.link_id = hashids.encode(self.event_id, self.from_user_id)

        super(LinkInvitation, self).save(*args, **kwargs)
