from __future__ import unicode_literals
from datetime import timedelta
import json
import re
from django.contrib.gis.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from push_notifications.models import APNSDevice
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
        message = ('{name} invited you to {activity} at {place} on {date}'
                   '\n--\nSent from Down (http://down.life/app)').format(
                   name=from_user.name, activity=event.title, place=place.name,
                   date=event_date)
    elif event.place:
        message = ('{name} invited you to {activity} at {place}'
                   '\n--\nSent from Down (http://down.life/app)').format(
                   name=from_user.name, activity=event.title, place=place.name)
    elif event.datetime:
        event_date = get_event_date(event, from_user.location)
        message = ('{name} invited you to {activity} on {date}'
                   '\n--\nSent from Down (http://down.life/app)').format(
                   name=from_user.name, activity=event.title, date=event_date)
    else:
        message = ('{name} invited you to {activity}'
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

        # Add the users to the Firebase members list.
        url = ('{firebase_url}/events/members/{event_id}/.json?auth='
               '{firebase_secret}').format(
                firebase_url=settings.FIREBASE_URL, event_id=event.id,
                firebase_secret=settings.FIREBASE_SECRET)
        json_invitations = json.dumps({
            invitation.to_user_id: True
            for invitation in self
        })
        requests.patch(url, json_invitations)

        # Don't notify the user who is sending the invitations, or users with
        # open invitations.
        invitations = [invitation for invitation in self
                       if invitation.to_user_id != from_user.id
                       and not invitation.open]

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
    previously_accepted = models.BooleanField(default=False)
    open = models.BooleanField(default=False)
    to_user_messaged = models.BooleanField(default=False)
    muted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = InvitationManager()

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
    # Since we're using PkOnlyPrimaryKeyRelatedFields, `invitation.to_user` and
    # `invitation.event` are objects with only primary keys. So we need to use
    # querysets to fetch the full objects.
    # TODO: Update the tests - move the notification tests to `test_views.py`.
    user = User.objects.get(id=invitation.to_user_id)
    event = Event.objects.get(id=invitation.event_id)

    # Don't notify the event creator that they accepted their own invitation.
    if user.id == event.creator_id:
        return

    if invitation.response == Invitation.ACCEPTED:
        message = '{name} is also down for {activity}'.format(
                name=user.name,
                activity=event.title)

        # Get all other members who have accepted their invitation, or haven't
        # responded yet, who've added the user as a friend. Always notify the
        # creator.
        invitations = Invitation.objects.filter(event=event) \
                .exclude(response=Invitation.DECLINED) \
                .exclude(to_user=user)
        member_ids = [invitation.to_user_id for invitation in invitations]
        added_me = Friendship.objects.filter(friend=user, user_id__in=member_ids)
        to_user_ids = [friendship.user_id for friendship in added_me]
        to_user_ids.append(event.creator_id)

        # This filter operation will only return unique devices.
        devices = APNSDevice.objects.filter(user_id__in=to_user_ids)
        devices.send_message(message)
    elif (invitation.response == Invitation.DECLINED
            and invitation.previously_accepted):
        # Only notify the user who invited them.
        message = '{name} isn\'t down for {activity}'.format(
                name=user.name,
                activity=event.title)
        devices = APNSDevice.objects.filter(user_id=invitation.from_user_id)
        devices.send_message(message)


class AllFriendsInvitation(models.Model):
    event = models.ForeignKey(Event)
    from_user = models.ForeignKey(User)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'from_user')

@receiver(post_save, sender=AllFriendsInvitation)
def send_open_invitation_notification(sender, instance, created, **kwargs):
    """
    Notify users with an open invitation to the event that the user is down for
    something.
    """
    all_friends_invitation = instance
    event = all_friends_invitation.event
    from_user = all_friends_invitation.from_user

    invitations = Invitation.objects.filter(event=event, from_user=from_user,
                                            open=True)
    user_ids = [invitation.to_user_id for invitation in invitations]
    devices = APNSDevice.objects.filter(user_id__in=user_ids)
    message = '{name} is down for {activity}'.format(name=from_user.name,
                                                     activity=event.title)
    devices.send_message(message, badge=1)
