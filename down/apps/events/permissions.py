from __future__ import unicode_literals
from rest_framework import permissions
from .models import Event, Invitation


class InviterWasInvited(permissions.BasePermission):
    """
    Global permission to only allow users who were invited to an event to
    invite other people.
    """

    def has_permission(self, request, view):
        import logging
        logger = logging.getLogger('console')
        logger.info('InviterWasInvited')
        logger.info(request.data)
        if request.data.has_key('invitations'):
            return True
        logger.info('got through')

        event_id = request.data.get('event')

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
        import logging
        logger = logging.getLogger('console')
        logger.info('WasInvited')
        logger.info(request.data)
        try:
            Invitation.objects.get(event=obj, to_user=request.user)
            return True
        except Invitation.DoesNotExist:
            return False


class IsFromUser(permissions.BasePermission):
    """
    Global permission to only allow the logged in user to be the
    `from_user` when creating an invitation.
    """

    def has_permission(self, request, view):
        import logging
        logger = logging.getLogger('console')
        logger.info('IsFromUser')
        logger.info(request.data)
        # This permission is only focused on creating an event.
        if request.method != 'POST':
            return True

        if request.data.has_key('invitations'):
            return True
        logger.info('got through')

        from_user_id = request.data.get('from_user')
        return request.user.id == from_user_id
