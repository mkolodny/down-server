from __future__ import unicode_literals
from rest_framework.test import APITestCase
from down.apps.auth.models import AuthCode


class AuthCodeTests(APITestCase):
    def setUp(self):
        pass

    def test_generates_default_auth_code(self):
        auth = AuthCode()

        # Valid auth code is six numbers
        self.assertRegexpMatches(auth.code, r'^\d{4}$')
