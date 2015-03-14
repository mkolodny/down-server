from __future__ import unicode_literals
from django.contrib.gis.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from push_notifications.models import APNSDevice
from down.apps.auth.models import User


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
    members = models.ManyToManyField(User, through='Invitation')


class Invitation(models.Model):
    to_user = models.ForeignKey(User)
    event = models.ForeignKey(Event)
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    previously_accepted = models.BooleanField(default=False)

@receiver(post_save, sender=Invitation)
def send_new_invitation_notification(sender, instance, created, **kwargs):
    """
    Send a push notification to users who receive an invite to an event.
    """
    if not created:
        return

    invitation = instance
    event = invitation.event
    
    # Don't notify the creator that they created an event.
    if invitation.to_user_id == event.creator_id:
        return

    message = '{name} is down for {activity}'.format(name=event.creator.name,
                                                     activity=event.title)
    devices = APNSDevice.objects.filter(user_id=invitation.to_user_id)
    devices.send_message(message)

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
    if not invitation.accepted:
        return
    # Only send a notification once per accepted event.
    if invitation.previously_accepted:
        return

    message = '{name} is also down for {activity}'.format(
            name=user.name,
            activity=event.title)
    # Exclude this user's accepted invitation.
    member_invitations = Invitation.objects.filter(
            accepted=True, event=event).exclude(id=invitation.id)
    member_ids = [
        invitation.to_user_id for invitation in member_invitations]
    # Notify the creator even if they haven't accepted the invitation.
    member_ids.append(event.creator_id)
    # This filter operation will only return unique devices.
    devices = APNSDevice.objects.filter(user_id__in=member_ids)
    # TODO: Catch exception if sending the message fails.
    devices.send_message(message)

    # Mark the user has having notified their friends.
    invitation.previously_accepted = True
    invitation.save()
