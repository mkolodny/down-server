import os
from .common import *


DEBUG = False
TEMPLATE_DEBUG = False

# DB
POSTGIS_VERSION = (2, 1, 5)

# GeoDjango
GEOS_LIBRARY_PATH = os.environ.get('GEOS_LIBRARY_PATH')
GDAL_LIBRARY_PATH = os.environ.get('GDAL_LIBRARY_PATH')

# Push notifications
PUSH_NOTIFICATIONS_SETTINGS.update({
    'APNS_CERTIFICATE': os.path.join(BASE_DIR, 'config/apns/prod/certkey.pem'),
})

# S3
INSTALLED_APPS += ('storages',)
STATICFILES_STORAGE = 'down.storage.S3CachedStorage'
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
AWS_S3_CUSTOM_DOMAIN = os.environ['AWS_S3_CUSTOM_DOMAIN']
AWS_HEADERS = {
    'x-amz-acl': 'public-read',
}
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = False
AWS_S3_SECURE_URLS = False
AWS_IS_GZIPPED = True
STATIC_URL = 'https://{domain}/'.format(domain=AWS_S3_CUSTOM_DOMAIN)

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django_bmemcached.memcached.BMemcached',
    },
}
