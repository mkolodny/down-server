from __future__ import unicode_literals
from rest_framework import permissions
from .models import Event, Invitation


class InviterWasInvited(permissions.BasePermission):
    """
    Global permission to only allow users who were invited to an event to
    invite other people.
    """

    def has_permission(self, request, view):
        # This permission is only focused on creating an event.
        if request.method != 'POST':
            return True

        # We're only allowing bulk creating invitations right now.
        if not request.data.has_key('invitations'):
            return False

        try:
            invitations = request.data['invitations']
            # TODO: Handle when no invitations are sent.
            event_id = invitations[0]['event']
            Invitation.objects.get(event_id=event_id, to_user=request.user)
            return True
        except Invitation.DoesNotExist:
            try:
                # Event creators can invite people even if their own invitation
                # to the event hasn't been saved yet.
                event = Event.objects.get(id=event_id)
                return event.creator_id == request.user.id
            except Event.DoesNotExist:
                # Since the event should exist, we want to return a 400
                # response. So let the user pass this round of validation.
                return True


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


class IsFromUser(permissions.BasePermission):
    """
    Global permission to only allow the logged in user to be the `from_user` when
    creating an invitation.
    """

    def has_permission(self, request, view):
        # This permission is only focused on creating an event.
        if request.method != 'POST':
            return True

        # We're only allowing bulk creating invitations right now.
        if not request.data.has_key('invitations'):
            return False

        invitations = request.data['invitations']
        # TODO: Handle when no invitations are sent.
        from_user_id = invitations[0]['from_user']
        return request.user.id == from_user_id


class OtherUsersNotDown(permissions.BasePermission):
    """
    Global permission to make sure that only the user can set their invitation
    response to "accepted".
    """

    def has_permission(self, request, view):
        # This permission is only focused on creating an event.
        if request.method != 'POST':
            return True

        # We're only allowing bulk creating invitations right now.
        if not request.data.has_key('invitations'):
            return False

        invitations = request.data['invitations']
        for invitation in invitations:
            to_user = invitation.get('to_user', request.user.id)
            response = invitation.get('response', Invitation.NO_RESPONSE)
            if to_user != request.user.id and response == Invitation.ACCEPTED:
                return False
        return True


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
