from django.conf.urls import patterns, include, url
from django.contrib import admin
from rest_framework import routers
from rallytap.apps.auth.views import (
    AuthCodeViewSet,
    FellowshipApplicationViewSet,
    LinfootFunnelViewSet,
    SessionViewSet,
    SocialAccountSync,
    UserUsernameDetail,
    UserViewSet,
    UserPhoneViewSet,
)
from rallytap.apps.client.views import (
    AppStoreView,
    ArticleView,
    FellowshipDemoView,
    FellowshipFoundersView,
    LandingView,
    PartialView,
    TermsView,
    WebAppView,
)
from rallytap.apps.events.views import (
    EventViewSet,
    InvitationViewSet,
    LinkInvitationViewSet,
    SuggestedEventsView,
)
from rallytap.apps.friends.views import FriendshipViewSet
from rallytap.apps.notifications.views import APNSDeviceViewSet, GCMDeviceViewSet

# TODO: Figure out how to split up the router urls into the individual apps.

# API
# With trailing slash appended:
router = routers.SimpleRouter()
router.register(r'devices/apns', APNSDeviceViewSet, base_name='apns')
router.register(r'devices/gcm', GCMDeviceViewSet, base_name='gcm')
router.register(r'authcodes', AuthCodeViewSet)
router.register(r'events', EventViewSet)
router.register(r'fellowships', FellowshipApplicationViewSet,
                base_name='fellowship')
router.register(r'friendships', FriendshipViewSet)
router.register(r'invitations', InvitationViewSet)
router.register(r'link-invitations', LinkInvitationViewSet,
                base_name='link-invitation')
router.register(r'phonenumbers', LinfootFunnelViewSet, base_name='phonenumbers')
router.register(r'sessions', SessionViewSet, base_name='session')
router.register(r'userphones', UserPhoneViewSet, base_name='userphone')
router.register(r'users', UserViewSet)
# Prints the (url, viewset, base_name) for each route.
#for route in router.registry:
#    print route
# Without trailing slash appended:
slashless_router = routers.SimpleRouter(trailing_slash=False)
slashless_router.registry = router.registry[:]

urlpatterns = patterns('',
    url(r'^api/social-account/?$', SocialAccountSync.as_view(),
        name='social-account-login'),
    url(r'^api/users/username/(?P<username>\w+)/?$', UserUsernameDetail.as_view(),
        name='user-username-detail'),
    url(r'^fellowship/?$', WebAppView.as_view(), name='web-app-fellowship'),
    url(r'^api/', include(slashless_router.urls)),
    url(r'^api/', include(router.urls)),
    #url(r'^$', LandingView.as_view(), name='landing'),
    url(r'^app/?$', AppStoreView.as_view(), name='app-store'),
    url(r'^$', WebAppView.as_view(), name='web-app-landing'),
    url(r'^e/\w+/?$', WebAppView.as_view(), name='web-app-event'),
    url(r'^login/?$', WebAppView.as_view(), name='web-app-login'),
    url(r'^i/\w+/?$', WebAppView.as_view(), name='web-app-invitation'),
    url(r'^partials/(?P<template_path>.+)', PartialView.as_view()),
    url(r'^terms/?$', TermsView.as_view(), name='terms'),
    url(r'^7-Epic-Music-Festivals$', ArticleView.as_view(), name='article'),
    url(r'^suggested-events$', SuggestedEventsView.as_view(),
        name='suggested-events'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^yc-fellowship/founders$', FellowshipFoundersView.as_view(),
        name='founders'),
    url(r'^yc-fellowship/demo$', FellowshipDemoView.as_view(), name='demo'),
)
