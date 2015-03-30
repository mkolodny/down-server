from __future__ import unicode_literals
from rest_framework import permissions
from .models import Invitation


class UserWasInvited(permissions.BasePermission):
    """
    Object-level permission to only allow users who were invited to an event to
    view the event.
    """

    def has_object_permission(self, request, view, obj):
        try:
            Invitation.objects.get(event=obj, to_user=request.user)
            return True
        except Invitation.DoesNotExist:
            return False
