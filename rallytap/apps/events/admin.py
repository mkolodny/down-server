from __future__ import unicode_literals
from django.contrib import admin
from .models import Event, Place, RecommendedEvent, SavedEvent


@admin.register(Event, Place, RecommendedEvent, SavedEvent)
class EventsAdmin(admin.ModelAdmin):
    pass
