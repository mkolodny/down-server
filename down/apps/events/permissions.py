from __future__ import unicode_literals
from rest_framework import permissions
from .models import Event, Invitation


class WasInvited(permissions.BasePermission):
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


class IsEventCreatorOrUpdateOnly(permissions.BasePermission):
    """
    Global permission to only allow the user who created an event to invite
    users to the event.
    """

    def has_permission(self, request, view):
        # This permission is only focused on creating an event.
        if request.method == 'PUT':
            return True

        event = Event.objects.get(id=request.data.get('event'))
        return event.creator_id == request.user.id
