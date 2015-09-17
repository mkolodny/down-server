from __future__ import unicode_literals
from datetime import datetime
import time
from rest_framework import relations, serializers
import pytz


class PkOnlyPrimaryKeyRelatedField(relations.PrimaryKeyRelatedField):

    def to_internal_value(self, data):
        """
        Return the related object as a model instance with only the id attribute
        set.

        Don't fetch the related object. Just make sure the primary key is an
        integer.
        """
        if type(data) != int:
            self.fail('incorrect_type', data_type=type(data).__name__)

        queryset = self.get_queryset()
        data = queryset.model(id=data)
        return data
