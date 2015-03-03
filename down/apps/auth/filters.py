from __future__ import unicode_literals
from django_filters import Filter, FilterSet
from .models import User


# TODO: Move this filter somewhere for general purpose.
class ListFilter(Filter):

    def filter(self, qs, value):
        if not value:
            return qs

        self.lookup_type = 'in'
        values = value.split(',')
        return super(ListFilter, self).filter(qs, values)


class UserFilter(FilterSet):
    ids = ListFilter(name='id')

    class Meta:
        model = User
        fields = ['ids']
