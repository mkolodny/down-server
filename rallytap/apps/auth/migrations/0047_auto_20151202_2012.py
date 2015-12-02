# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations
from rallytap.apps.auth import utils


def meteor_login(apps, schema_editor):
    User = apps.get_model('down_auth', 'User')
    Token = apps.get_model('authtoken', 'Token')

    # Don't run the migration in dev.
    if settings.ENV == 'dev':
        return
    
    for token in Token.objects.all():
        utils.meteor_login(token)

class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0046_auto_20151125_0216'),
    ]

    operations = [
    ]
