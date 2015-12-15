from __future__ import unicode_literals
from django.contrib.gis.db import models
from rallytap.apps.auth.models import User


class Place(models.Model):
    name = models.TextField()
    geo = models.PointField(null=True, blank=True)

    def __unicode__(self):
        return unicode(self.name)


class RecommendedEvent(models.Model):
    title = models.TextField()
    datetime = models.DateTimeField(null=True, blank=True)
    place = models.ForeignKey(Place, null=True, blank=True)

    def __unicode__(self):
        return unicode(self.title)


class Event(models.Model):
    title = models.TextField()
    creator = models.ForeignKey(User, related_name='creators')
    # Set to true once an event chat has been deleted on the meteor server.
    expired = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    datetime = models.DateTimeField(null=True, blank=True)
    place = models.ForeignKey(Place, null=True, blank=True)
    friends_only = models.BooleanField(default=False)
    recommended_event = models.ForeignKey(RecommendedEvent, null=True,
                                          blank=True)

    def __unicode__(self):
        return unicode(self.title)


class SavedEvent(models.Model):
    user = models.ForeignKey(User)
    event = models.ForeignKey(Event)
    # where the user was when they saved the event
    location = models.PointField()
    # when the event was saved
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')

    def __unicode__(self):
        return unicode(self.event.title)
