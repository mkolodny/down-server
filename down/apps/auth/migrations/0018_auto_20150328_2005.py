# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import phonenumber_field.modelfields
import down.apps.auth.models


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0017_authcode'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPhoneNumber',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(unique=True, max_length=128)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='authcode',
            name='code',
            field=models.TextField(default=down.apps.auth.models.default_auth_code),
            preserve_default=True,
        ),
    ]
