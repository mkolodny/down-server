from __future__ import unicode_literals
from django.http import Http404
from django.shortcuts import render
from django.template.base import TemplateDoesNotExist
from django.views.generic.base import RedirectView, TemplateView
from rest_framework.views import APIView


class TermsView(TemplateView):
    template_name = 'terms.html'


class LandingView(TemplateView):
    template_name = 'landing.html'


class AppStoreView(RedirectView):
    url = 'http://bnc.lt/m/cdhqhLhSSm'
    permanent = False


class ArticleView(TemplateView):
    template_name = 'festivals.html'


class FellowshipFoundersView(TemplateView):
    template_name = 'founders.html'


class FellowshipDemoView(TemplateView):
    template_name = 'demo.html'


class WebAppView(TemplateView):
    template_name = 'web-app.html'


class PartialView(APIView):

    def get(self, request, format=None, **kwargs):
        try:
            return render(request, kwargs['template_path'])
        except TemplateDoesNotExist:
            raise Http404
