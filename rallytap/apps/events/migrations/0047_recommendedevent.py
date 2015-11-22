# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0046_auto_20151121_0215'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecommendedEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.TextField()),
                ('datetime', models.DateTimeField(null=True, blank=True)),
                ('place', models.ForeignKey(blank=True, to='events.Place', null=True)),
            ],
        ),
    ]
