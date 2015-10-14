from __future__ import unicode_literals
from django.conf import settings
from rest_framework import authentication
from rest_framework import exceptions


class MeteorAuthentication(authentication.BaseAuthentication):
    """
    Raise an exception if the request isn't authenticated with the meteor server
    key.
    """

    def authenticate(self, request):
        meteor_token = 'Token {meteor_key}'.format(meteor_key=settings.METEOR_KEY)
        if request.META.get('HTTP_AUTHORIZATION') != meteor_token:
            raise exceptions.AuthenticationFailed('Bath auth token')
        return None
