from __future__ import unicode_literals
from datetime import datetime
import time
from rest_framework import serializers
import pytz


class UnixEpochDateField(serializers.DateTimeField):

    def to_representation(self, value):
        """
        Return epoch time for a datetime object or ``None``.
        """
        try:
            return int(time.mktime(value.timetuple()))
        except (AttributeError, TypeError):
            return None

    def to_internal_value(self, value):
        return datetime.utcfromtimestamp(int(value)).replace(tzinfo=pytz.utc)
