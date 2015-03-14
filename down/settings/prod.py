import os
from .common import *


DEBUG = False
TEMPLATE_DEBUG = False

# DB
POSTGIS_VERSION = (2, 1, 3)

# GeoDjango
GEOS_LIBRARY_PATH = os.environ.get('GEOS_LIBRARY_PATH')
GDAL_LIBRARY_PATH = os.environ.get('GDAL_LIBRARY_PATH')

# Push notifications
PUSH_NOTIFICATIONS_SETTINGS = {
    'APNS_CERTIFICATE': os.path.join(BASE_DIR, 'config/apns/aps_production.cer'),
    'APNS_KEY': os.path.join(BASE_DIR, 'config/apns/aps_production.p12'),
}
