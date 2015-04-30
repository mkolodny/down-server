from __future__ import unicode_literals
from django_filters import FilterSet
from .models import User
from down.apps.utils.filters import ListFilter


class UserFilter(FilterSet):
    ids = ListFilter(name='id')

    class Meta:
        model = User
        fields = ['ids', 'username']
