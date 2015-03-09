from __future__ import unicode_literals
from django.db import models
from django.contrib.gis.db import models
from down.apps.auth.models import User


class Place(models.Model):
    name = models.TextField()
    geo = models.PointField(null=True, blank=True)


class Event(models.Model):
    title = models.TextField()
    creator = models.ForeignKey(User, related_name='event_creator')
    canceled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    datetime = models.DateTimeField(null=True, blank=True)
    place = models.ForeignKey(Place, null=True, blank=True) # Make this a ForeignKey
    description = models.TextField(null=True, blank=True)
    members = models.ManyToManyField(User, through='Invitation')


class Invitation(models.Model):
    to_user = models.ForeignKey(User)
    event = models.ForeignKey(Event)
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
