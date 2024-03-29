from __future__ import unicode_literals
from django.db import models
from rallytap.apps.auth.models import User


class Friendship(models.Model):
    user = models.ForeignKey(User, related_name='user+')
    friend = models.ForeignKey(User, related_name='friend+')
    since = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'friend')

    def __unicode__(self):
        return '{user} -> {friend}'.format(user=unicode(self.user.name),
                                           friend=unicode(self.friend.name))
