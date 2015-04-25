from __future__ import unicode_literals
from django_filters import Filter, FilterSet
from .models import Event
from down.apps.utils.filters import UnixEpochDateFilter


class EventFilter(FilterSet):
    min_updated_at = UnixEpochDateFilter(name='updated_at', lookup_type='gte')

    class Meta:
        model = Event
        fields = ['min_updated_at']
