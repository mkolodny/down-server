from __future__ import unicode_literals
from django.conf import settings
from django.contrib.gis.measure import D
from django.db.models import Q
from django_filters import Filter, FilterSet
from rest_framework.filters import BaseFilterBackend
from rallytap.apps.utils.filters import UnixEpochDateFilter
from .models import Event, Place


class EventFilter(FilterSet):
    min_updated_at = UnixEpochDateFilter(name='updated_at', lookup_type='gte')

    class Meta:
        model = Event
        fields = ['min_updated_at']


class NearbyPlaceFilter(BaseFilterBackend):
    """
    Only return events that are either nearby the current user, or don't have a
    place.
    """
    def filter_queryset(self, request, queryset, view):
        return queryset.select_related('place').filter(
                Q(place__isnull=True) |
                Q(place__geo__distance_lte=(request.user.location,
                                            D(mi=settings.NEARBY_DISTANCE))))
