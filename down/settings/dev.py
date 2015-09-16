from .common import *


DEBUG = True
TEMPLATE_DEBUG = True

# DB
POSTGIS_VERSION = (2, 1, 3)

# API
REST_FRAMEWORK['TEST_REQUEST_DEFAULT_FORMAT'] = 'json'

# Push notifications
PUSH_NOTIFICATIONS_SETTINGS.update({
    'APNS_CERTIFICATE': os.path.join(BASE_DIR, 'config/apns/dev/certkey.pem'),
    'APNS_HOST': 'gateway.sandbox.push.apple.com',
    'APNS_FEEDBACK_HOST': 'feedback.sandbox.push.apple.com',
})

# Static files
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'down/client/build'),
) + STATICFILES_DIRS
