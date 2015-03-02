# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SocialAccount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('provider', models.SmallIntegerField(choices=[(1, 'facebook')])),
                ('uid', models.TextField()),
                ('last_login', models.DateTimeField(auto_now=True)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('provided_data', jsonfield.fields.JSONField(default=b'{}')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(default=django.utils.timezone.now, verbose_name='last login')),
                ('email', models.EmailField(unique=True, max_length=75)),
                ('name', models.TextField()),
                ('username', models.TextField(unique=True, null=True)),
                ('image_url', models.URLField()),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('location', models.TextField(null=True, blank=True)),
                ('notifyToken', models.TextField(null=True, blank=True)),
                ('firebaseToken', models.TextField()),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='socialaccount',
            name='user',
            field=models.ForeignKey(to='down_auth.User'),
            preserve_default=True,
        ),
    ]
