# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0003_auto_20150301_2212'),
    ]

    operations = [
        migrations.CreateModel(
            name='Friend',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('since', models.DateTimeField(auto_now_add=True)),
                ('user1', models.ForeignKey(related_name='friend1', to='down_auth.User')),
                ('user2', models.ForeignKey(related_name='friend2', to='down_auth.User')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FriendRequests',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('response', models.SmallIntegerField(blank=True, null=True, choices=[(1, 'yes'), (2, 'no')])),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('from_user', models.ForeignKey(related_name='friend_request_from_user', to='down_auth.User')),
                ('to_user', models.ForeignKey(related_name='friend_request_to_user', to='down_auth.User')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
