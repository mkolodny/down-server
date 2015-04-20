# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def accepted_to_status(apps, schema_editor):
    Invitation = apps.get_model('events', 'Invitation')
    for invitation in Invitation.objects.all():
        if invitation.accepted:
            invitation.status = Invitation.ACCEPTED
        else:
            invitation.status = Invitation.NO_RESPONSE
        invitation.save()

class Migration(migrations.Migration):

    dependencies = [
        ('events', '0012_auto_20150420_0537'),
    ]

    operations = [
        migrations.RunPython(accepted_to_status)   
    ]
