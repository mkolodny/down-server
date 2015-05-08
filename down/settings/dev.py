from .common import *


DEBUG = True
TEMPLATE_DEBUG = True

# DB
POSTGIS_VERSION = (2, 1, 3)

# API
REST_FRAMEWORK['TEST_REQUEST_DEFAULT_FORMAT'] = 'json'

# Push notifications
PUSH_NOTIFICATIONS_SETTINGS = {
    'APNS_CERTIFICATE': os.path.join(BASE_DIR, 'config/apns/dev/certkey.pem'),
}
