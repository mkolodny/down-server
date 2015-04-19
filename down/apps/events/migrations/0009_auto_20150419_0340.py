# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


def set_from_user(apps, schema_editor):
    Invitation = apps.get_model('events', 'Invitation')
    for invitation in Invitation.objects.all():
        invitation.from_user_id = invitation.event.creator_id
        invitation.save()

class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('events', '0008_invitation_previously_accepted'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='from_user',
            field=models.ForeignKey(related_name='related_from_user+', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='invitation',
            name='to_user',
            field=models.ForeignKey(related_name='related_to_user+', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.RunPython(set_from_user)
    ]
