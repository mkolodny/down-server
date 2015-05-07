from __future__ import unicode_literals
from datetime import timedelta
import json
import re
from django.contrib.gis.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from push_notifications.models import APNSDevice
import requests
from twilio.rest import TwilioRestClient
from down.apps.auth.models import User, UserPhone
from down.apps.notifications.utils import notify_users

EARTHTOOLS_RE = re.compile(r'<offset>(-?\d+)</offset>')


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
    members = models.ManyToManyField(User, through='Invitation',
                                     through_fields=('event', 'to_user'))

    def get_member_devices(self, except_user, notify_responses):
        """
        Get all members who have accepted their invitation, or haven't responded
        yet, except the `except_user`.

        Get the creator whether or not they've accepted the invitation.
        """
        invitations = Invitation.objects.filter(response__in=notify_responses,
                                                event=self)
        invitations = invitations.exclude(to_user=except_user)
        member_ids = [invitation.to_user_id for invitation in invitations]

        # This filter operation will only return unique devices.
        return APNSDevice.objects.filter(user_id__in=member_ids)


def get_invite_sms(from_user, event):
    """
    Return the message to SMS to invite the `from_user` to `event`.
    """
    if event.place:
        place = event.place

    if event.datetime and event.place:
        event_dt = get_offset_dt(event.datetime, place.geo)
        event_date = event_dt.strftime('%A, %b. %-d @ %-I:%M %p')
        message = ('{name} invited you to {activity} at {place} on {date}'
                   '\n--\nSent from Down (http://down.life/app)').format(
                   name=from_user.name, activity=event.title, place=place.name,
                   date=event_date)
    elif event.place:
        message = ('{name} invited you to {activity} at {place}'
                   '\n--\nSent from Down (http://down.life/app)').format(
                   name=from_user.name, activity=event.title, place=place.name)
    elif event.datetime:
        event_dt = get_offset_dt(event.datetime, from_user.location)
        event_date = event_dt.strftime('%A, %b. %-d @ %-I:%M %p')
        message = ('{name} invited you to {activity} on {date}'
                   '\n--\nSent from Down (http://down.life/app)').format(
                   name=from_user.name, activity=event.title, date=event_date)
    else:
        message = ('{name} invited you to {activity}'
                   '\n--\nSent from Down (http://down.life/app)').format(
                   name=from_user.name, activity=event.title)
    return message

def get_offset_dt(dt, point):
    """
    Return a datetime offset based on the timezone where `point` lays.
    """
    coords = point.coords
    url = 'http://www.earthtools.org/timezone/{lat}/{long}'.format(
            lat=coords[0], long=coords[1])
    r = requests.get(url)
    match = EARTHTOOLS_RE.search(r.content)
    if not match:
        # Return the original, non-offset datetime.
        return dt
    offset = match.group(1)
    offset_dt = dt + timedelta(hours=int(offset))
    return offset_dt

class InvitationManager(models.Manager):

    def get_queryset(self):
        return InvitationQuerySet(self.model)


class InvitationQuerySet(models.query.QuerySet):

    def send(self):
        """
        Send push notifications / SMS notifying people that they were invited to
        an event. All of the invitations must be from the same user, for the same
        event.
        """
        if self.count() == 0:
            return

        # Get the first invitation to use to grab the user sending the invitations,
        # and the event.
        first_invitation = self.first()
        from_user = first_invitation.from_user
        event = first_invitation.event

        # Make sure that all of the invitations are from the same user, for the
        # same event.
        assert all((invitation.from_user_id == from_user.id) for invitation in self)
        assert all((invitation.event_id == event.id) for invitation in self)

        # Don't notify the user who is sending the invitations.
        invitations = [invitation for invitation in self
                       if invitation.to_user_id != from_user.id]

        # Add the users to the Firebase members list.
        url = ('{firebase_url}/events/members/{event_id}/.json?auth='
               '{firebase_secret}').format(
                firebase_url=settings.FIREBASE_URL, event_id=event.id,
                firebase_secret=settings.FIREBASE_SECRET)
        json_invitations = json.dumps({
            invitation.to_user_id: True
            for invitation in invitations
        })
        requests.patch(url, json_invitations)

        # Send users with devices push notifications.
        message = '{name} invited you to {activity}'.format(name=from_user.name,
                                                            activity=event.title)
        user_ids = [invitation.to_user_id for invitation in invitations]
        devices = APNSDevice.objects.filter(user_id__in=user_ids)
        devices.send_message(message, badge=1)

        # Text message everyone else their invitation.
        message = get_invite_sms(from_user, event)
        device_user_ids = [device.user_id for device in devices]
        sms_user_ids = [invitation.to_user_id for invitation in invitations
                        if invitation.to_user_id not in device_user_ids]
        userphones = UserPhone.objects.filter(user_id__in=sms_user_ids)
        client = TwilioRestClient(settings.TWILIO_ACCOUNT, settings.TWILIO_TOKEN)
        for userphone in userphones:
            phone = unicode(userphone.phone)
            client.messages.create(to=phone, from_=settings.TWILIO_PHONE,
                                   body=message)


class Invitation(models.Model):
    from_user = models.ForeignKey(User, related_name='related_from_user+')
    to_user = models.ForeignKey(User, related_name='related_to_user+')
    event = models.ForeignKey(Event)
    NO_RESPONSE = 0
    ACCEPTED = 1
    DECLINED = 2
    RESPONSE_CHOICES = (
        (NO_RESPONSE, 'no response'),
        (ACCEPTED, 'accepted'),
        (DECLINED, 'declined'),
    )
    response = models.SmallIntegerField(choices=RESPONSE_CHOICES,
                                        default=NO_RESPONSE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    previously_accepted = models.BooleanField(default=False)

    objects = InvitationManager()

    class Meta:
        unique_together = ('to_user', 'event')

    def save(self, *args, **kwargs):
        super(Invitation, self).save(*args, **kwargs)

        if self.response == self.ACCEPTED and not self.previously_accepted:
            self.previously_accepted = True
            self.save(update_fields=['previously_accepted'])


@receiver(post_save, sender=Invitation)
def send_invitation_accept_notification(sender, instance, created, **kwargs):
    """
    Send a push notification to users who are already down for the event when
    a user accepts the invitation.
    """
    if kwargs['update_fields'] == frozenset(['previously_accepted']):
        # if we're only updating the previously_accepted field, don't
        # send anything to anyone. Shhhhhhh
        return

    invitation = instance
    user = invitation.to_user
    event = invitation.event
    if user.id == event.creator_id:
        return

    if invitation.response == Invitation.NO_RESPONSE:
        return
    elif invitation.response == Invitation.DECLINED:
        # Only notify the event creator.
        message = '{name} isn\'t down for {activity}'.format(
                name=user.name,
                activity=event.title)
        notify_users([event.creator_id], message)
    elif invitation.response == Invitation.ACCEPTED:
        # The user is down.
        message = '{name} is also down for {activity}'.format(
                name=user.name,
                activity=event.title)

    # Get all other members who have accepted their invitation, or haven't responded
    # yet, except the `current_user`. Get the creator whether or not they've
    # accepted the invitation.
    notify_responses = [Invitation.ACCEPTED, Invitation.NO_RESPONSE]
    devices = event.get_member_devices(user, notify_responses)
    devices.send_message(message)
