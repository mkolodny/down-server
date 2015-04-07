from django.conf.urls import patterns, include, url
from django.contrib import admin
from rest_framework import routers
from down.apps.auth.views import (
    AppStoreView,
    AuthCodeViewSet,
    LandingView,
    LinfootFunnelViewSet,
    SessionView,
    SocialAccountLogin,
    TermsView,
    UserUsernameDetail,
    UserViewSet,
    UserPhoneNumberView,
)
from down.apps.events.views import EventViewSet, InvitationViewSet
from down.apps.friends.views import FriendshipViewSet
from down.apps.notifications.views import APNSDeviceViewSet

# TODO: Figure out how to split up the router urls into the individual apps.

# API
# With trailing slash appended:
router = routers.SimpleRouter()
router.register(r'apnsdevices', APNSDeviceViewSet)
router.register(r'authcodes', AuthCodeViewSet)
router.register(r'events', EventViewSet)
router.register(r'friendships', FriendshipViewSet)
router.register(r'invitations', InvitationViewSet)
router.register(r'phonenumbers', LinfootFunnelViewSet, base_name='phonenumbers')
router.register(r'users', UserViewSet)
# Prints the (url, viewset, base_name) for each route.
#for route in router.registry:
#    print route
# Without trailing slash appended:
slashless_router = routers.SimpleRouter(trailing_slash=False)
slashless_router.registry = router.registry[:]

urlpatterns = patterns('',
    url(r'^api/userphones/phones/?$', UserPhoneNumberView.as_view(),
        name='userphone'),
    url(r'^api/social-account/?$', SocialAccountLogin.as_view(),
        name='social-account-login'),
    url(r'^api/users/username/(?P<username>\w+)/?$', UserUsernameDetail.as_view(),
        name='user-username-detail'),
    url(r'^api/sessions/?$', SessionView.as_view(), name='session'),
    url(r'^api/', include(slashless_router.urls)),
    url(r'^api/', include(router.urls)),
    url(r'^terms/?$', TermsView.as_view(), name='terms'),
    url(r'^$', LandingView.as_view(), name='landing'),
    url(r'^app/?$', AppStoreView.as_view(), name='app-store'),
    url(r'^admin/', include(admin.site.urls)),
)
