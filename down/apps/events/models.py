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

@receiver(post_save, sender=Invitation)
def send_new_invitation_notification(sender, instance, created, **kwargs):
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
