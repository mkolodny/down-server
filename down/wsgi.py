import os

# Django needs to know which settings module to use
environ = os.environ['ENV']
settings_module = 'down.settings.{environ}'.format(environ=environ)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

from django.core.wsgi import get_wsgi_application
from dj_static import Cling

application = Cling(get_wsgi_application())
