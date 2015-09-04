from django.conf.urls import patterns, include, url
from django.contrib import admin
from rest_framework import routers
from down.apps.auth.views import (
    AppStoreView,
    ArticleView,
    AuthCodeViewSet,
    FellowshipDemoView,
    FellowshipFoundersView,
    LandingView,
    LinfootFunnelViewSet,
    SessionView,
    SocialAccountSync,
    TermsView,
    UserUsernameDetail,
    UserViewSet,
    UserPhoneViewSet,
)
from down.apps.events.views import (
    EventViewSet,
    InvitationViewSet,
    LinkInvitationViewSet,
    SuggestedEventsView,
)
from down.apps.friends.views import FriendshipViewSet
from down.apps.notifications.views import APNSDeviceViewSet, GCMDeviceViewSet

# TODO: Figure out how to split up the router urls into the individual apps.

# API
# With trailing slash appended:
router = routers.SimpleRouter()
router.register(r'devices/apns', APNSDeviceViewSet, base_name='apns')
router.register(r'devices/gcm', GCMDeviceViewSet, base_name='gcm')
router.register(r'authcodes', AuthCodeViewSet)
router.register(r'events', EventViewSet)
router.register(r'friendships', FriendshipViewSet)
router.register(r'invitations', InvitationViewSet)
router.register(r'link-invitations', LinkInvitationViewSet,
                base_name='link-invitation')
router.register(r'phonenumbers', LinfootFunnelViewSet, base_name='phonenumbers')
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
    url(r'^api/sessions/?$', SessionView.as_view(), name='session'),
    url(r'^yc-fellowship/founders$', FellowshipFoundersView.as_view(),
        name='founders'),
    url(r'^yc-fellowship/demo$', FellowshipDemoView.as_view(), name='demo'),
    url(r'^api/', include(slashless_router.urls)),
    url(r'^api/', include(router.urls)),
    url(r'^terms/?$', TermsView.as_view(), name='terms'),
    #url(r'^$', LandingView.as_view(), name='landing'),
    url(r'^$', AppStoreView.as_view(), name='landing'),
    url(r'^7-Epic-Music-Festivals$', ArticleView.as_view(), name='article'),
    url(r'^suggested-events$', SuggestedEventsView.as_view(),
        name='suggested-events'),
    url(r'^app/?$', AppStoreView.as_view(), name='app-store'),
    url(r'^admin/', include(admin.site.urls)),
)
