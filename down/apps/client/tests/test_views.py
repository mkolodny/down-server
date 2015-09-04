from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class TermsTests(APITestCase):

    def test_get(self):
        url = reverse('terms')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'terms.html')


class LandingTests(APITestCase):

    """
    def test_get(self):
        url = reverse('landing')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'landing.html')
    """

    def test_redirect(self):
        url = reverse('landing')
        response = self.client.get(url)
        app_store_url = ('https://itunes.apple.com/us/app/down-connect-people'
                         '-around/id969040287?mt=8')
        self.assertRedirects(response, app_store_url,
                             fetch_redirect_response=False)


class AppStoreTests(APITestCase):

    def test_redirect(self):
        url = reverse('app-store')
        response = self.client.get(url)
        app_store_url = ('https://itunes.apple.com/us/app/down-connect-people'
                         '-around/id969040287?mt=8')
        self.assertRedirects(response, app_store_url,
                             fetch_redirect_response=False)


class ArticleTests(APITestCase):

    def test_get(self):
        url = reverse('article')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'festivals.html')


class FellowshipFoundersTests(APITestCase):

    def test_get(self):
        url = reverse('founders')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'founders.html')


class FellowshipDemoTests(APITestCase):

    def test_get(self):
        url = reverse('demo')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'demo.html')


class AppTests(APITestCase):

    def test_get(self):
        url = reverse('web-app')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'web-app.html')
