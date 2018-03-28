# Django settings for 'cerarisk' project.
import os

DEBUG = True

ADMINS = (
    ('Carola Kaiser', 'ckaiser@cct.lsu.edu'),
)
MANAGERS = ADMINS

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'cera',
        'USER': 'cera',
        'PASSWORD': 'XXz1dGAFpfs5E#Kaalm@LKHc',
		#'nccera-1.renci.org',
        'HOST': '152.54.1.81',
        'PORT': '5432',
 		'ATOMIC_REQUEST': True
    }
}

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'z#*ko$jc^f5xo1&%&+0*oyywkfma6kh*=^1g4o3_!44evk0-qr'
ALLOWED_HOSTS = ['*']
TIME_ZONE = 'America/Chicago'     #CST
DATETIME_FORMAT = 'N d, Y, H:i'
USE_TZ = True
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False
# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = False

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# path of settings.py -> set all paths in view.py relative to this.
# e.g. for download legendimg
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

LOGIN_URL = '/cerarisk/accounts/login/'
LOGIN_REDIRECT_URL = '/'
PHONENUMBER_DB_FORMAT = 'RFC3966'
AUTH_PROFILE_MODULE = 'cera_data.UserProfile'

ROOT_URLCONF = 'cera_data.urls'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a trailing slash.
# Examples: "http://media.lawrence.com", "http://example.com/media/"
# MEDIA_URL = 'http://ceraserver.lsu.edu/static/admin/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
#STATIC_ROOT = os.path.join(BASE_DIR, 'cera_data/static/')

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
STATIC_URL = 'https://cera.coastalrisk.live/cera_risk/'

# Additional locations of static files
STATICFILES_DIRS = (
    "C:/msw/Apache/htdocs_cerarisk/cera_risk"
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder'
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cera_data.adcircrun',
    'cera_data.ceracgi',
    'cera_data.home',
    'localflavor'
    #'debug_toolbar'
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
]

#SECURE_SSL_REDIRECT = True #redirects every http request to https
SESSION_COOKIE_SECURE = True # browsers ensure that the cookie is only sent under an HTTPS connection
CSRF_COOKIE_SECURE = True # browsers ensure that the cookie is only sent under an HTTPS connection
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages'
            ],
            'debug': DEBUG
        },
    }
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['null'],
            'level': 'DEBUG',
            'propagate': True
        },
    }
}

CERA_ENV = {
    'GOOGLE_MAPS_KEY' : 'AIzaSyADfBA05E4I5N2GCpEQqMvQwOngVbaKuxQ',
    # set global environment variables, avoid DNS lookup
    'MAPSERVER_WMSHOST' : '130.39.22.158',
    'MAPSERVER_DBHOST' : '152.54.1.81',
    # redirect json file + legend; twister goes to local django, all other to ncrenci-1
    'REDIRECT_DBHOST' : '130.39.13.135',
    #'CERA_ADMINMODE' : 'yes',
    'CERA_EXPAND_BASEURL' : '0',            # only needed for development server to add /cerarisk
    										# e.g. twister.cct.lsu.edu/cerarisk
    										# production servers have this with a rewrite rule
    										# e.g. cera.coastalrisk.live -> host/cerarisk
    'CERA_BASE_PATH' : 'cera_risk',   		# cera website (htdocs) base directory ('cera' or 'cera_risk')
    'CERA_CGI_PATH' : 'cgi-cera',		# cgi path (cgi-cera)
    'DJANGO_BASE_PATH' : 'cerarisk',   		# django alias name as defined in conf ('cera-data' or 'cerarisk')
    'DJANGO_CERACGI_PATH' : 'cera_data', 	# path to ceracgi for *.py scripts on wms_hosts to create tiles (django alias name: only important for development website: use cera_data instead of cerarisk because cerarisk is not available on wms_hosts yet)
    'DJANGO_ADMIN_PATH' : 'cerarisk' 		# directory that holds the 'templates' folder

}

EMAIL_USE_TLS = True
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.coastalrisk.live'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'info@coastalrisk.live' # this is just for authentication of the email host
EMAIL_HOST_PASSWORD = 'WXToqHqteyC2oCZ8WCTP'
DEFAULT_FROM_EMAIL = 'info@coastalrisk.live' #for password_reset

