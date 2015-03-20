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
    'down.apps.auth',
    'down.apps.events',
    'down.apps.friends',
    'down.apps.notifications',
    'push_notifications',
)
MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)
ROOT_URLCONF = 'down.urls'
WSGI_APPLICATION = 'down.wsgi.application'
ADMINS = (
    ('Viraj Sinha', 'virajosinha@gmail.com'),
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
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'down/static'),
)

# Templates
TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'down/templates'),
)

# Auth
AUTH_USER_MODEL = 'down_auth.User'
AUTHENTICATION_BACKENDS = ('down.apps.auth.backends.UserInstanceBackend',)
PASSWORD_HASHERS = ('django.contrib.auth.hashers.SHA1PasswordHasher',)

# Facebook
FACEBOOK_APP_ID = os.environ['FACEBOOK_APP_ID']
FACEBOOK_APP_SECRET = os.environ['FACEBOOK_APP_SECRET']

# Firebase
FIREBASE_SECRET = os.environ['FIREBASE_SECRET']

# Push notifications
PUSH_NOTIFICATIONS_SETTINGS = {
    'APNS_CERTIFICATE': os.path.join(BASE_DIR, 'config/apns/certkey.pem'),
}
