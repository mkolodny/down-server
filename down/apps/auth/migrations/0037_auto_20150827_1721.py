# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def first_last_names(apps, schema_editor):
    SocialAccount = apps.get_model('down_auth', 'SocialAccount')
    for account in SocialAccount.objects.all():
        user = account.user
        user.first_name = account.profile['first_name']
        user.last_name = account.profile['last_name']
        user.save()

class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0036_remove_user_authtoken'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='first_name',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='last_name',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='name',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.RunPython(first_last_names),
    ]
