from __future__ import unicode_literals
from rest_framework import permissions


class IsCreator(permissions.BasePermission):
    """
    Object-level permission to only allow the creator to edit an event.
    """

    def has_object_permission(self, request, view, obj):
        # This permission only applies to editing an event.
        if request.method != 'PUT':
            return True

        event = obj
        if event.creator_id != request.user.id:
            return False
        return True
