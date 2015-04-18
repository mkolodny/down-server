# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def clear_auth_codes(apps, schema_editor):
    AuthCode = apps.get_model('down_auth', 'AuthCode')
    AuthCode.objects.all().delete()

def clear_user_phones(apps, schema_editor):
    UserPhoneNumber = apps.get_model('down_auth', 'UserPhoneNumber')
    UserPhoneNumber.objects.all().delete()

def clear_social_accounts(apps, schema_editor):
    SocialAccount = apps.get_model('down_auth', 'SocialAccount')
    SocialAccount.objects.all().delete()

def clear_users(apps, schema_editor):
    User = apps.get_model('down_auth', 'User')
    User.objects.all().delete()

def clear_tokens(apps, schema_editor):
    Token = apps.get_model('authtoken', 'Token')
    Token.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0026_remove_user_facebook_friends'),
        ('friends', '0009_auto_20150418_2321'),
        ('events', '0009_auto_20150418_2321'),
        ('notifications', '0001_initial'),
        ('authtoken', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(clear_auth_codes),
        migrations.RunPython(clear_user_phones),
        migrations.RunPython(clear_social_accounts),
        migrations.RunPython(clear_users),
        migrations.RunPython(clear_tokens),
    ]
