from __future__ import unicode_literals
from django.conf import settings
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class TermsTests(APITestCase):

    def test_get(self):
        url = reverse('terms')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'terms.html')


class AppStoreTests(APITestCase):

    def test_redirect(self):
        url = reverse('app-store')
        response = self.client.get(url)
        app_store_url = 'http://bnc.lt/m/cdhqhLhSSm'
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


class WebAppTests(APITestCase):

    def test_get_landing(self):
        url = reverse('web-app-landing')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.context['BRANCH_API_KEY'],
                         settings.BRANCH_API_KEY)
        self.assertEqual(response.context['FACEBOOK_APP_ID'],
                         settings.FACEBOOK_APP_ID)
        self.assertEqual(response.context['API_ROOT'],
                         settings.API_ROOT)
        self.assertEqual(response.context['MIXPANEL_TOKEN'],
                         settings.MIXPANEL_TOKEN)
        self.assertEqual(response.context['METEOR_URL'],
                         settings.METEOR_URL)
        self.assertTemplateUsed(response, 'web-app.html')

    def test_get_fellowship(self):
        url = reverse('web-app-fellowship')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.context['BRANCH_API_KEY'],
                         settings.BRANCH_API_KEY)
        self.assertEqual(response.context['FACEBOOK_APP_ID'],
                         settings.FACEBOOK_APP_ID)
        self.assertEqual(response.context['API_ROOT'],
                         settings.API_ROOT)
        self.assertEqual(response.context['MIXPANEL_TOKEN'],
                         settings.MIXPANEL_TOKEN)
        self.assertEqual(response.context['METEOR_URL'],
                         settings.METEOR_URL)
        self.assertTemplateUsed(response, 'web-app.html')


class PartialTestCase(APITestCase):

    def test_get(self):
        response = self.client.get('/partials/landing/landing.html')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'landing/landing.html')

    def test_get_404(self):
        response = self.client.get('/partials/blah')
        self.assertEqual(response.status_code, 404)


class PrivacyPolicyTests(APITestCase):

    def test_get(self):
        url = reverse('privacy')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # It should return the privacy policy as an inline pdf.
        self.assertEqual(response['Content-Disposition'],
                         'inline;filename=rallytap-privacy-policy.pdf')
