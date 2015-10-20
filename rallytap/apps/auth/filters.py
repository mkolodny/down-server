from __future__ import unicode_literals
from django_filters import FilterSet
from .models import User
from rallytap.apps.utils.filters import ListFilter, IgnoreCaseCharFilter


class UserFilter(FilterSet):
    ids = ListFilter(name='id')
    username = IgnoreCaseCharFilter(name='username')

    class Meta:
        model = User
        fields = ['ids', 'username']
