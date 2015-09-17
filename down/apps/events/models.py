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
from down.apps.auth.models import User, UserPhone
from down.apps.friends.models import Friendship

GEONAMES_RE = re.compile(r'<timezoneId>(.+?)</timezoneId>')


class Place(models.Model):
    name = models.TextField()
    geo = models.PointField(null=True, blank=True)


class Event(models.Model):
    title = models.TextField()
    creator = models.ForeignKey(User, related_name='creators')
    canceled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    datetime = models.DateTimeField(null=True, blank=True)
    place = models.ForeignKey(Place, null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    members = models.ManyToManyField(User, through='Invitation',
                                     through_fields=('event', 'to_user'))


def get_invite_sms(from_user, event):
    """
    Return the message to SMS to invite the `from_user` to `event`.
    """
    if event.place:
        place = event.place

    if event.datetime and event.place:
        event_date = get_event_date(event, place.geo)
        message = ('{name} suggested: {activity} at {place} on {date}'
                   '\n--\nSent from Down (http://down.life/app)').format(
                   name=from_user.name, activity=event.title, place=place.name,
                   date=event_date)
    elif event.place:
        message = ('{name} suggested: {activity} at {place}'
                   '\n--\nSent from Down (http://down.life/app)').format(
                   name=from_user.name, activity=event.title, place=place.name)
    elif event.datetime:
        event_date = get_event_date(event, from_user.location)
        message = ('{name} suggested: {activity} on {date}'
                   '\n--\nSent from Down (http://down.life/app)').format(
                   name=from_user.name, activity=event.title, date=event_date)
    else:
        message = ('{name} suggested: {activity}'
                   '\n--\nSent from Down (http://down.life/app)').format(
                   name=from_user.name, activity=event.title)
    return message

def get_event_date(event, point):
    """
    Return a date string to include in the text message invitation.
    """
    event_dt = get_local_dt(event.datetime, point)
    if event_dt:
        event_date = event_dt.strftime('%A, %b. %-d @ %-I:%M %p')
    else:
        event_date = event.datetime.strftime('%A, %b. %-d')
    return event_date

def get_local_dt(dt, point):
    """
    Return a local datetime based on the timezone where `point` lays.

    If there is an error connecting to the GeoNames API, return None.
    """
    coords = point.coords
    url = ('http://api.geonames.org/timezone?lat={lat}&lng={long}'
           '&username=mkolodny').format(lat=coords[0], long=coords[1])
    r = requests.get(url)
    match = GEONAMES_RE.search(r.content)
    if not match:
        return None
    timezone = match.group(1)
    local_tz = pytz.timezone(timezone)
    local_dt = dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_dt

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
    previously_accepted = models.BooleanField(default=False)
    muted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('to_user', 'event')

    def save(self, *args, **kwargs):
        super(Invitation, self).save(*args, **kwargs)

        if self.response == self.ACCEPTED and not self.previously_accepted:
            self.previously_accepted = True
            self.save(update_fields=['previously_accepted'])

        # Update the event whenever we update an invitation from anything other
        # than no response.
        if self.response != self.NO_RESPONSE:
            # The event is an id-only model object, so we need to fetch the whole
            # thing.
            event = Event.objects.get(id=self.event.id)
            event.save()


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
