# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0029_auto_20150502_2012'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPhone',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(unique=True, max_length=128)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='userphonenumber',
            name='user',
        ),
        migrations.DeleteModel(
            name='UserPhoneNumber',
        ),
    ]
