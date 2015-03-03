from django.conf.urls import patterns, include, url
from django.contrib import admin
from rest_framework import routers
from down.apps.auth.views import (
    SocialAccountLogin,
    UserUsernameDetail,
    UserViewSet,
)
from down.apps.events.views import EventViewSet, InvitationViewSet

# TODO: Figure out how to split up the router urls into the individual apps.
router = routers.SimpleRouter()
router.register(r'users', UserViewSet)
router.register(r'events', EventViewSet)
router.register(r'invitations', InvitationViewSet)

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/social-account$', SocialAccountLogin.as_view(),
        name='social-account-login'),
    url(r'^api/users/username/(?P<username>\w+)$', UserUsernameDetail.as_view(),
        name='user-username-detail'),
    url(r'^api/', include(router.urls)),
)
