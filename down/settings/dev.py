from .common import *


DEBUG = False
TEMPLATE_DEBUG = False

# API
REST_FRAMEWORK = {
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

# DB
POSTGIS_VERSION = (2, 1, 3)

# Staticfiles
STATIC_ROOT = STATICFILES_DIRS[0]
