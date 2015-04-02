from __future__ import unicode_literals
from rest_framework import permissions


class UserIsCurrentUser(permissions.BasePermission):
    """
    Global permission to only allow the logged in user to get or create an
    object.

    Note: Requires request data/query_params with a `user` attribute.
    """

    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user.id == request.data.get('user')
        elif request.method == 'GET':
            return unicode(request.user.id) == request.query_params.get('user')
        else:
            return True
