from __future__ import unicode_literals
import re
from django import forms
from django.contrib import admin
from django.contrib.gis.db import models
from .models import Event, Place, RecommendedEvent, SavedEvent


class LatLngInput(forms.TextInput):

    def value_from_datadict(self, data, files, name):
        point = data.get(name, None)
        if point is None or not re.match(r'-?\d+\.?(\d+)?, ?-?\d+\.?(\d+)?', point):
            return point
        lat, lng = point.split(',')
        return 'POINT({lat} {lng})'.format(lat=lat, lng=lng)


@admin.register(Event, Place, RecommendedEvent, SavedEvent)
class EventsAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.PointField: {'widget': LatLngInput},
    }
