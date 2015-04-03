from __future__ import unicode_literals
from django.contrib.gis.db import models
from django.db import models
from down.apps.auth.models import User


class Friendship(models.Model):
    # TODO: Figure out why the only one friend is getting a new many-to-many friend
    # when saving a friendship.
    user = models.ForeignKey(User, related_name='user+')
    friend = models.ForeignKey(User, related_name='friend+')
    since = models.DateTimeField(auto_now_add=True)
    acknowledged = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'friend')
