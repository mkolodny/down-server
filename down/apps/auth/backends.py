from __future__ import unicode_literals


class UserInstanceBackend(object):

    def authenticate(self, user=None):
        return user
