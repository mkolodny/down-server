# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('down_auth', '0022_remove_user_friend_requests'),
        ('friends', '0006_auto_20150402_2210'),
    ]

    operations = [
        migrations.CreateModel(
            name='AddedMe',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('added_by', models.ForeignKey(related_name='added_by+', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(related_name='user+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='friendrequests',
            name='from_user',
        ),
        migrations.RemoveField(
            model_name='friendrequests',
            name='to_user',
        ),
        migrations.DeleteModel(
            name='FriendRequests',
        ),
        migrations.AlterUniqueTogether(
            name='addedme',
            unique_together=set([('user', 'added_by')]),
        ),
    ]
