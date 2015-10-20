# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('down_auth', '0009_remove_user_friends'),
        ('friends', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Friendship',
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
        migrations.RemoveField(
            model_name='friend',
            name='user1',
        ),
        migrations.RemoveField(
            model_name='friend',
            name='user2',
        ),
        migrations.DeleteModel(
            name='Friend',
        ),
    ]
