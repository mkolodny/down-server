from __future__ import unicode_literals
from datetime import datetime
from django_filters import Filter, FilterSet, CharFilter
import pytz


class IgnoreCaseCharFilter(CharFilter):

    def filter(self, qs, value):
        self.lookup_type = 'iexact'
        return super(IgnoreCaseCharFilter, self).filter(qs, value)


class ListFilter(Filter):

    def filter(self, qs, value):
        if not value:
            return qs

        self.lookup_type = 'in'
        values = value.split(',')
        return super(ListFilter, self).filter(qs, values)


class UnixEpochDateFilter(Filter):

    def filter(self, qs, value):
        if not value:
            return qs

        # Convert the value to a Python datetime object.
        value = datetime.utcfromtimestamp(int(value)).replace(tzinfo=pytz.utc)
        return super(UnixEpochDateFilter, self).filter(qs, value)
