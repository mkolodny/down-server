from __future__ import unicode_literals
from django.views.generic.base import RedirectView, TemplateView


class TermsView(TemplateView):
    template_name = 'terms.html'


class LandingView(TemplateView):
    template_name = 'landing.html'


class AppStoreView(RedirectView):
    url = ('https://itunes.apple.com/us/app/down-connect-people-around/id'
           '969040287?mt=8')
    permanent = False


class ArticleView(TemplateView):
    template_name = 'festivals.html'


class FellowshipFoundersView(TemplateView):
    template_name = 'founders.html'


class FellowshipDemoView(TemplateView):
    template_name = 'demo.html'
