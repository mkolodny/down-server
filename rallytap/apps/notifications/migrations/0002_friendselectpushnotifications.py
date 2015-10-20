# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FriendSelectPushNotifications',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lastest_sent_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('friend', models.ForeignKey(related_name='related_friend', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(related_name='related_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
