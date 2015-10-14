from __future__ import unicode_literals
from django.db import models
from django.utils import timezone
from down.apps.auth.models import User


class FriendSelectPushNotification(models.Model):
    user = models.ForeignKey(User, related_name='related_user')
    friend = models.ForeignKey(User, related_name='related_friend')
    latest_sent_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'friend')
