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
        ('events', '0011_auto_20150419_1426'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='status',
            field=models.SmallIntegerField(default=0, choices=[(0, 'no response'), (1, 'accepted'), (2, 'declined')]),
            preserve_default=True,
        ),
        migrations.RunPython(accepted_to_status),
        migrations.RemoveField(
            model_name='invitation',
            name='accepted',
        ),
    ]
