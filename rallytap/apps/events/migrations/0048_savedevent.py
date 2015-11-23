# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('events', '0047_recommendedevent'),
    ]

    operations = [
        migrations.CreateModel(
            name='SavedEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('location', django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(to='events.Event')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
