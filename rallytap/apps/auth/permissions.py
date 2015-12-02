from __future__ import unicode_literals
from django.conf import settings
from rest_framework import permissions


class IsCurrentUserOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow the current logged in user to edit a user
    object.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj == request.user


class IsStaff(permissions.BasePermission):
    """
    Only allow staff members to touch a resource.
    """

    def has_permission(self, request, view):
        return request.user.is_staff


class IsMeteor(permissions.BasePermission):
    """
    Only allow the meteor server to access an object.
    """

    def has_permission(self, request, view):
        return request.user.id == settings.METEOR_USER_ID
