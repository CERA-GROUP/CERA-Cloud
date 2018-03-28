import os, sys

sys.path.append('I:/django/cerarisk')
sys.path.append('I:/django/cerarisk/cera_data')
sys.path.append('I:/CERA/programs')
sys.path.append('C:/ms4w/Apache/cgi-bin')
sys.path.append('C:/Python27/Lib/site-packages')

os.environ['DJANGO_SETTINGS_MODULE'] = "cera_data.settings"

from django.core.wsgi import get_wsgi_application
_application = get_wsgi_application()

def application(environ, start_response):
  os.environ['GOOGLEKEY'] = environ['GOOGLE_MAPS_KEY']
  return _application(environ, start_response)

