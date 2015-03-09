from __future__ import unicode_literals
from django.contrib.gis.db import models
from django.db import models
from down.apps.auth.models import User


class Friendship(models.Model):
    # TODO: Figure out why the only one friend is getting a new many-to-many friend
    # when saving a friendship.
    user1 = models.ForeignKey(User, related_name='friend1s+')
    user2 = models.ForeignKey(User, related_name='friend2s+')
    since = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')


class FriendRequests(models.Model):
    from_user = models.ForeignKey(User, related_name='from_users')
    to_user = models.ForeignKey(User, related_name='to_users')
    YES = 1
    NO = 2
    RESPONSE_TYPE = (
        (YES, 'yes'),
        (NO, 'no'),
    )
    response = models.SmallIntegerField(null=True, blank=True,
                                        choices=RESPONSE_TYPE)
    datetime = models.DateTimeField(auto_now_add=True)
