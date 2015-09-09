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

        if request.data.has_key('invitations'):
            # TODO: Handle when no invitations are sent.
            # TODO: Handle when the event id wasn't sent.
            invitations = request.data['invitations']
            event_id = request.data['event']
        else:
            event_id = request.data['event']

        try:
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


class AllFriendsInviterWasInvited(permissions.BasePermission):
    """
    Global permission to only allow users who were invited to an event to
    invite all of their friends.
    """

    def has_permission(self, request, view):
        # This permission is only focused on creating an event.
        if request.method != 'POST':
            return True

        try:
            event_id = request.data['event']
            Invitation.objects.get(event_id=event_id, to_user=request.user)
            return True
        except Invitation.DoesNotExist:
            return False


class LinkInviterWasInvited(permissions.BasePermission):
    """
    Global permission to only allow users who were invited to an event to
    share a link to the event.
    """

    def has_permission(self, request, view):
        # This permission is only focused on creating an event.
        if request.method != 'POST':
            return True

        try:
            event_id = request.data['event']
            Invitation.objects.get(event_id=event_id, to_user=request.user)
            return True
        except Invitation.DoesNotExist:
            return False


class LinkInviterIsFromUser(permissions.BasePermission):
    """
    Global permission to only allow users who were invited to an event to
    share a link to the event.
    """

    def has_permission(self, request, view):
        # This permission is only focused on creating an event.
        if request.method != 'POST':
            return True

        from_user_id = request.data['from_user']
        return from_user_id == request.user.id


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    The request is authenticated as a user, or is a read-only request.
    """

    def has_permission(self, request, view):
        safe_methods =  ['GET', 'HEAD', 'OPTIONS']
        return request.method in safe_methods or request.user.is_authenticated()
