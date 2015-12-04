# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations


def create_meteor_user_token(apps, schema_editor):
    User = apps.get_model('down_auth', 'User')
    Token = apps.get_model('authtoken', 'Token')
    user = User.objects.get(id=settings.METEOR_USER_ID)
    token = Token(user=user, key=settings.METEOR_KEY)
    token.save()
        
class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0049_auto_20151204_1804'),
    ]

    operations = [
        migrations.RunPython(create_meteor_user_token),
    ]
