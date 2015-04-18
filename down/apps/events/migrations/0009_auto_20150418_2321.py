# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def clear_invitations(apps, schema_editor):
    Invitation = apps.get_model('events', 'Invitation')
    Invitation.objects.all().delete()

def clear_events(apps, schema_editor):
    Event = apps.get_model('events', 'Event')
    Event.objects.all().delete()

def clear_places(apps, schema_editor):
    Place = apps.get_model('events', 'Place')
    Place.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('events', '0008_invitation_previously_accepted'),
    ]

    operations = [
        migrations.RunPython(clear_invitations),
        migrations.RunPython(clear_events),
        migrations.RunPython(clear_places),
    ]
