# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def set_points(apps, schema_editor):
    User = apps.get_model('down_auth', 'User')
    Invitation = apps.get_model('events', 'Invitation')
    Event = apps.get_model('events', 'Event')
    invitations = Invitation.objects.all()
    expired_events = Event.objects.filter(expired=True)
    expired_events_set = {event.id for event in expired_events}
    for user in User.objects.filter(username__isnull=False):
        # Everyone starts out with 100 points.
        points = 100

        # 1 point for sending an invitation.
        sent_invitations = invitations.filter(from_user=user)
        points += sent_invitations.count()

        # 5 points for saying you're down.
        accepted_invitations = invitations.filter(to_user=user, response=1)
        points += 5 * accepted_invitations.count()

        # -5 points for not responding.
        no_response_invitations = invitations.filter(to_user=user, response=0)
        for invitation in no_response_invitations:
            if invitation.event_id in expired_events_set:
                points -= 5

        user.points = points
        user.save()

class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0043_auto_20151109_1533'),
    ]

    operations = [
        migrations.RunPython(set_points),
    ]
