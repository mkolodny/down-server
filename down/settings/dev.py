from .common import *


DEBUG = True
TEMPLATE_DEBUG = True

# DB
POSTGIS_VERSION = (2, 1, 3)

# Push notifications
PUSH_NOTIFICATIONS_SETTINGS = {
    'APNS_CERTIFICATE': os.path.join(BASE_DIR, 'config/apns/dev/certkey.pem'),
}
