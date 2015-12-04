from __future__ import unicode_literals
from django.conf import settings
from rest_framework import permissions


class IsMeteor(permissions.BasePermission):
    """
    Only allow the meteor server to access a view.
    """

    def has_permission(self, request, view):
        print request.user.id
        print settings.METEOR_USER_ID
        return request.user.id == settings.METEOR_USER_ID
