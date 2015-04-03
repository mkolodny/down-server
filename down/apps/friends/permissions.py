from __future__ import unicode_literals
from rest_framework import permissions


class UserIsCurrentUser(permissions.BasePermission):
    """
    Global permission to only allow the logged in user to create an object. Also,
    only allow one of the two friends to request an object.

    Note: Requires request data/query_params with a `user` attribute.
    """

    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user.id == request.data.get('user')
        elif request.method == 'GET':
            friends = (
                request.query_params.get('user'),
                request.query_params.get('friend'),
            )
            return unicode(request.user.id) in friends
        else:
            return True
