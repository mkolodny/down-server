from .common import *


DEBUG = True
TEMPLATE_DEBUG = True

# DB
POSTGIS_VERSION = (2, 1, 3)

# Push notifications
PUSH_NOTIFICATIONS_SETTINGS = {
    'APNS_CERTIFICATE': os.path.join(BASE_DIR, 'config/apns/dev/certkey.pem'),
}

# API
REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.AcceptHeaderVersioning',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}
