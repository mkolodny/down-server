from __future__ import unicode_literals
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from push_notifications.models import APNSDevice
from down.apps.auth.models import User


class Friendship(models.Model):
    user = models.ForeignKey(User, related_name='user+')
    friend = models.ForeignKey(User, related_name='friend+')
    since = models.DateTimeField(auto_now_add=True)
    acknowledged = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'friend')

@receiver(post_save, sender=Friendship)
def send_new_friendship_notification(sender, instance, created, **kwargs):
    """
    Send a push notification to the user who was added as a friend
    """

    if not created:
        return

    friendship = instance

    # check if one leg of this friendship already exists in the database
    if Friendship.objects.filter(user=friendship.friend, friend=friendship.user):
        message = '{name} added you back!'.format(name=friendship.user.name)
    else:
        message = '{name} added you as a friend!'.format(name=friendship.user.name)

    devices = APNSDevice.objects.filter(user_id=friendship.friend.id)
    devices.send_message(message)
    extra = {'message': message}
    devices.send_message(None, extra=extra)


"""
class FacebookFriendship(models.Model):
    user = models.ForeignKey(User, related_name='user+')
    friend = models.ForeignKey(User, related_name='friend+')
"""
