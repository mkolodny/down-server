from django.conf.urls import patterns, include, url
from django.contrib import admin
from rest_framework import routers
from down.apps.auth.views import (
    SocialAccountLogin,
    UserUsernameDetail,
    UserViewSet,
    TermsView,
    FunnelView,
)
from down.apps.events.views import EventViewSet, InvitationViewSet
from down.apps.notifications.views import APNSDeviceViewSet

# TODO: Figure out how to split up the router urls into the individual apps.

# API
# With trailing slash appended:
router = routers.SimpleRouter()
router.register(r'users', UserViewSet)
router.register(r'events', EventViewSet)
router.register(r'invitations', InvitationViewSet)
router.register(r'apnsdevices', APNSDeviceViewSet)
# Without trailing slash appended:
slashless_router = routers.SimpleRouter(trailing_slash=False)
slashless_router.registry = router.registry[:]

urlpatterns = patterns('',
    url(r'^api/social-account/?$', SocialAccountLogin.as_view(),
        name='social-account-login'),
    url(r'^api/users/username/(?P<username>\w+)/?$', UserUsernameDetail.as_view(),
        name='user-username-detail'),
    url(r'^api/', include(slashless_router.urls)),
    url(r'^api/', include(router.urls)),
    url(r'^terms/?$', TermsView.as_view(), name='terms'),
    url(r'^$', FunnelView.as_view(), name='funnel'),
    url(r'^admin/', include(admin.site.urls)),
)
