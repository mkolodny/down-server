from __future__ import division, unicode_literals
import os
import dj_database_url


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
SECRET_KEY = os.environ['SECRET_KEY']
ALLOWED_HOSTS = ['*']
ENV = os.environ['ENV']

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'rallytap.apps.auth',
    'rallytap.apps.client',
    'rallytap.apps.events',
    'rallytap.apps.friends',
    'rallytap.apps.notifications',
    'push_notifications',
    'rest_framework.authtoken',
    'corsheaders',
)
MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # Has to come before common middleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)
ROOT_URLCONF = 'rallytap.urls'
WSGI_APPLICATION = 'rallytap.wsgi.application'
ADMINS = (
    ('Andrew Linfoot', 'ajlin500@gmail.com'),
    ('Michael Kolodny', 'michaelckolodny@gmail.com'),
)
APPEND_SLASH = False

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Database
DATABASES = {'default': dj_database_url.config()}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_ROOT = 'staticfiles'
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'rallytap/static'),
)

# Templates
TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'rallytap/templates'),
    os.path.join(BASE_DIR, 'rallytap/client/app'),
)

# Auth
AUTH_USER_MODEL = 'down_auth.User'
AUTHENTICATION_BACKENDS = ('rallytap.apps.auth.backends.UserInstanceBackend',)
PASSWORD_HASHERS = ('django.contrib.auth.hashers.SHA1PasswordHasher',)

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': ('File "%(pathname)s", line %(lineno)s, in %(funcName)s\n' +
                       '  %(message)s'),
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        }
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'console': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    }
}

# API
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.AcceptHeaderVersioning',
}
API_ROOT = os.environ['API_ROOT']

# CORS
CORS_ORIGIN_ALLOW_ALL = True

# Meteor server
METEOR_KEY = os.environ['METEOR_KEY']
METEOR_URL = os.environ['METEOR_URL']
METEOR_USER_ID = -1

# Facebook
FACEBOOK_APP_ID = os.environ['FACEBOOK_APP_ID']
FACEBOOK_APP_SECRET = os.environ['FACEBOOK_APP_SECRET']

# Twilio
TWILIO_ACCOUNT = os.environ['TWILIO_ACCOUNT']
TWILIO_TOKEN = os.environ['TWILIO_TOKEN']
TWILIO_PHONE = os.environ['TWILIO_PHONE']

# Hashids
HASHIDS_SALT = os.environ['HASHIDS_SALT']

# Push notifications
PUSH_NOTIFICATIONS_SETTINGS = {
    'GCM_API_KEY': os.environ['GCM_API_KEY'],
}

# Branch
BRANCH_API_KEY = os.environ['BRANCH_API_KEY']

# Mixpanel
MIXPANEL_TOKEN = os.environ['MIXPANEL_TOKEN']

# Querying
# 10: miles away that is still considered nearby
# 24,901: circumference of the earth in miles
# 360: degrees in a circle
NEARBY_RADIUS = (10 / 24901) * 360
