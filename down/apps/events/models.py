from __future__ import unicode_literals
from django.contrib.gis.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import json
from push_notifications.models import APNSDevice
import requests
from twilio.rest import TwilioRestClient
from down.apps.auth.models import User, UserPhoneNumber


class Place(models.Model):
    name = models.TextField()
    geo = models.PointField(null=True, blank=True)


class Event(models.Model):
    title = models.TextField()
    creator = models.ForeignKey(User, related_name='creators')
    canceled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    datetime = models.DateTimeField(null=True, blank=True)
    place = models.ForeignKey(Place, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    members = models.ManyToManyField(User, through='Invitation',
                                     through_fields=('event', 'from_user'))

    def get_relevant_member_devices(self, except_user):
        """
        Get all members who have accepted their invitation, except the
        `except_user`.

        Get the creator whether or not they've accepted the invitation.
        """
        # Exclude this user's accepted invitation.
        member_invitations = Invitation.objects.filter(
                status=Invitation.ACCEPTED,
                event=self).exclude(to_user=except_user)
        member_ids = [
            invitation.to_user_id for invitation in member_invitations]
        # Notify the creator even if they haven't accepted the invitation.
        member_ids.append(self.creator_id)

        # This filter operation will only return unique devices.
        return APNSDevice.objects.filter(user_id__in=member_ids)


class Invitation(models.Model):
    from_user = models.ForeignKey(User, related_name='related_from_user+')
    to_user = models.ForeignKey(User, related_name='related_to_user+')
    event = models.ForeignKey(Event)
    NO_RESPONSE = 0
    ACCEPTED = 1
    DECLINED = 2
    STATUS_TYPES = (
        (NO_RESPONSE, 'no response'),
        (ACCEPTED, 'accepted'),
        (DECLINED, 'declined'),
    )
    status = models.SmallIntegerField(choices=STATUS_TYPES,
                                      default=NO_RESPONSE)
    created_at = models.DateTimeField(auto_now_add=True)
    previously_accepted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('to_user', 'event')

@receiver(post_save, sender=Invitation)
def send_new_invitation_notification(sender, instance, created, **kwargs):
    """
    Notify users who receive an invite to an event. If the user has the app
    installed, send them a push notification. Otherwise, text them the
    invitation.
    """
    if not created:
        return

    invitation = instance
    event = invitation.event
    
    # Don't notify the creator that they created an event.
    if invitation.to_user_id == event.creator_id:
        return

    to_user = invitation.to_user
    creator = event.creator
    if to_user.username:
        # The user has the app installed, so send them a push notification.
        message = '{name} is down for {activity}'.format(name=creator.name,
                                                         activity=event.title)
        devices = APNSDevice.objects.filter(user=to_user)
        devices.send_message(message)
        extra = {'message': message}
        devices.send_message(None, extra=extra)
    else:
        # The user doesn't have the app installed, so text them the invitation.
        if event.datetime and event.place:
            event_date = event.datetime.strftime('%A, %b. %-d @ %-I:%M %p')
            message = ('{name} is down for {activity} at {place} on {date}'
                       '\n--\nSent from Down (http://down.life/app)').format(
                       name=creator.name, activity=event.title,
                       place=event.place.name, date=event_date)
        elif event.place:
            message = ('{name} is down for {activity} at {place}'
                       '\n--\nSent from Down (http://down.life/app)').format(
                       name=creator.name, activity=event.title,
                       place=event.place.name)
        elif event.datetime:
            event_date = event.datetime.strftime('%A, %b. %-d @ %-I:%M %p')
            message = ('{name} is down for {activity} on {date}'
                       '\n--\nSent from Down (http://down.life/app)').format(
                       name=creator.name, activity=event.title,
                       date=event_date)
        else:
            message = ('{name} is down for {activity}'
                       '\n--\nSent from Down (http://down.life/app)').format(
                       name=creator.name, activity=event.title)
        phone = unicode(UserPhoneNumber.objects.get(user=to_user).phone)
        client = TwilioRestClient(settings.TWILIO_ACCOUNT, settings.TWILIO_TOKEN)
        client.messages.create(to=phone, from_=settings.TWILIO_PHONE,
                               body=message)

@receiver(post_save, sender=Invitation)
def add_user_to_firebase_members_list(sender, instance, created, **kwargs):
    """
    Update the firebase members list table with the new user so that the firebase
    security rules will allow them to read and write messages to the event chat
    """
    if not created:
        return

    invitation = instance

    url = ('{firebase_url}/events/members/{event_id}/.json?auth='
           '{firebase_secret}').format(
            firebase_url = settings.FIREBASE_URL,
            event_id = invitation.event_id,
            firebase_secret = settings.FIREBASE_SECRET)
    data = {invitation.to_user_id: True}
    requests.patch(url, json.dumps(data))


@receiver(post_save, sender=Invitation)
def send_invitation_accept_notification(sender, instance, created, **kwargs):
    """
    Send a push notification to users who are already down for the event when
    a user accepts the invitation.
    """
    invitation = instance
    user = invitation.to_user
    event = invitation.event

    # Only notify other users if the user accepted the invitation.
    if invitation.status != Invitation.ACCEPTED:
        return
    # Only send a notification once per accepted event.
    if invitation.previously_accepted:
        return

    message = '{name} is also down for {activity}'.format(
            name=user.name,
            activity=event.title)
    devices = event.get_relevant_member_devices(user)

    # TODO: Catch exception if sending the message fails.
    devices.send_message(message)

    extra = {'message': message}
    devices.send_message(None, extra=extra)

    # Mark the user has having notified their friends.
    invitation.previously_accepted = True
    invitation.save()
