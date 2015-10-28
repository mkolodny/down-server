from __future__ import unicode_literals
from django.conf import settings
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

    def get_context_data(self, **kwargs):
        context = super(WebAppView, self).get_context_data(**kwargs)
        context['BRANCH_API_KEY'] = settings.BRANCH_API_KEY
        context['FACEBOOK_APP_ID'] = settings.FACEBOOK_APP_ID
        context['API_ROOT'] = settings.API_ROOT
        context['MIXPANEL_TOKEN'] = settings.MIXPANEL_TOKEN
        return context


class PartialView(APIView):

    def get(self, request, format=None, **kwargs):
        try:
            return render(request, kwargs['template_path'])
        except TemplateDoesNotExist:
            raise Http404
