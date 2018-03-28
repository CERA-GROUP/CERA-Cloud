from django.contrib.auth.models import User
from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.urls import reverse

from cera_data.home.forms import CeraProForm
from cera_data.settings import CERA_ENV
import os
import urllib

###############################################################################
def getenv(d, key, deflt):
  if d.has_key(key):
    return d[key]
  return deflt

def expand_baseurl(cera):
  expand_baseurl = "0"
  if (getenv(CERA_ENV, "CERA_EXPAND_BASEURL", "0") != "0"):
    expand_baseurl = "1"

  if expand_baseurl == "0":
    baseurl = "/"
  else:
    baseurl = "/cerarisk/"

  return baseurl

def get_adminmode():
  adminmode = "0"
  # CERA_ENV ise set in settings.py
  if (getenv(CERA_ENV, "CERA_ADMINMODE", "0") != "0"):
    adminmode = "1"

  return adminmode

EXTENTS = {
#   latlongSouthWest  latlongNorthEast
  "_atlantic" : [ "14.0,-98", "45.0,-60" ],
#  "_gulf" : [ "21,-97", "37,-74" ],
  "al" : [ "29.5,-88.5", "31.0,-87.5" ],
  "la" : [ "28.5,-93.5", "31.5,-88.8" ],
  "laorleans" : [ "29.81,-90.33", "30.08,-89.87" ],
  "ms" : [ "29.5,-89.7", "31.0,-88.5" ],
  "nj" : [ "38.78,-75.62", "42.77,-71.84" ],
  "noc" : [ "34.1,-78.8", "37.0,-75.4" ],
  "va" : [ "36.49,-77.5", "39.84,-74.85" ],
  "flw" : [ "24.7,-87.3", "30.9,-81.1" ],
  "flwtampa" : [ "27.57,-82.85", "28.06,-82.38" ],
  "pr" : [ "17.9,-67.6", "18.6,-64.6" ],
  "ri" : [ "41.0, -72.5", "42.4, -70.0" ],
  "tx" : [ "26.5,-96.5", "30.0,-92.5" ],
  "txhouston" : [ "29.17,-95.56", "29.94,-94.68" ],
  "parishes_la" : [ "28.7,-93.7", "31.2,-89.0" ],
  "vermillion" : [ "29.5,-92.8", "30.2,-91.9" ]
#	"custom" : [ "14.0,-98", "45.0,-60" ]
}

WMS_HOST = getenv(CERA_ENV, "MAPSERVER_WMSHOST","")
QUERY_SOURCE = "http://" + WMS_HOST + "/cgi-cera/cera_wms.cgi?"
# WMS_SOURCE = "http://" + WMS_HOST + "/cgi-cera/cera_wms.cgi?"
WMS_SOURCE = "http://" + WMS_HOST + "/cgi-cera/cera_wms_tiled.cgi?"
WMS_ANI_SOURCE = "http://" + WMS_HOST + "/cgi-cera/cera_ani_tiled.cgi?"

def has_url_entry(urldata, key):
  val = urldata.get(key)
  if val is None:
    return False
  elif len(val) == 0:
    return False
  return True

def get_url_entry(urldata, key, deflt):
  val = urldata.get(key)
  if val is None:
    val = deflt
  elif len(val) == 0:
    val = deflt
  return val

def get_dev_site(cera):
  dev_site = 0   #pub, nc_ng, nc, ng
  if cera == 'pl':
    dev_site = 4
  elif cera == 'st':
    dev_site = 3
#  elif cera == 'pro':
#    dev_site = 2
  elif cera == 'dev':
    dev_site = 1

  return dev_site

# CERA site specific initial values for the form (no initial value in form.py)
def form_dictionary(cera):
  # ['pub', 'st', 'dev', 'nc_ng']:
  initial = {'tz':'!utc', 'ne':'45,-60', 'sw':'14,-98', 'unit':'!ft'}

  if cera == 'ng':
    initial = {'tz':'cdt', 'ne':'37,-74', 'sw':'21,-97'}
  elif cera in ['nc', 'ri']:
    initial = {'tz':'!edt', 'ne':'45,-60', 'sw':'14,-98', 'unit':'!ft'}
  elif cera == 'pr':
    initial = {'tz':'!ast', 'ne':'45,-60', 'sw':'14,-98', 'unit':'!ft'}
  elif cera == 'pl':
    initial = {'tz':'!cdt', 'ne':'31.2,-89', 'sw':'28.7,-93.7', 'unit':'!ft'}

  return initial

# CERA site specific mapextent for html template
# keys must be in corret order to appear correctly in maptools
def set_mapextent_data(cera):
  # ['pub', 'dev', 'st', 'nc_ng']
  mapextent_data = {
    "_atlantic": "East + Gulf Coast",
    "al": "Alabama",
    "flw": "Florida West",
    "flwtampa": "-- Tampa",
    "la": "Louisiana",
    "laorleans": "-- New Orleans",
    "ms": "Mississippi",
    "nj": "New Jersey",
    "noc": "North Carolina",
    "ri": "Rhode Island",
    "tx": "Texas",
    "txhouston": "-- Houston",
    "va": "Virginia"
    #"custom": "- Custom -", default_entry: true
  }

  if cera == 'nc':
    mapextent_data = {
      "_atlantic": "East + Gulf Coast",
      "nj": "New Jersey",
      "noc": "North Carolina",
      "ri": "Rhode Island",
      #"pr": "Puerto Rico",
      "va": "Virginia"
    }
  elif cera == 'ng':
    mapextent_data = {
      "_atlantic": "East + Gulf Coast",
      "al": "Alabama",
      "flw": "Florida West",
      "flwtampa": "-- Tampa",
      "la": "Louisiana",
      "laorleans": "-- New Orleans",
      "ms": "Mississippi",
      "tx": "Texas",
      "txhouston": "-- Houston"
    }
  elif cera == 'pr':
    mapextent_data = {
      "_atlantic": "East + Gulf Coast",
      "pr": "Puerto Rico"
    }
  elif cera == 'ri':
    mapextent_data = {
      "_atlantic": "East + Gulf Coast",
      "ri": "Rhode Island"
    }
  elif cera == 'pl':
    mapextent_data = {
      "_atlantic": "East + Gulf Coast",
      "parishes_la" : "Louisiana",
      "vermillion": "Vermillion Parish"
    }

  return mapextent_data

# Google analytics
def analytics_nr(cera):
  if cera == 'nc_ng' or cera == 'nc' or cera == 'ng':
    nr = "UA-16277394-12"
  elif cera == 'pub':
    nr = "UA-16277394-18"
#  elif cera == 'ng':
#    nr = "UA-16277394-9"
#  elif cera == 'nc':
#    nr = "UA-16277394-6"
  elif cera == 'dev':
    nr = "UA-16277394-10"
  elif cera == 'pr':
    nr = "UA-16277394-13"
  elif cera == 'ri':
    nr = "UA-16277394-15"
  elif cera == 'st':
    nr = "UA-16277394-16"
  elif cera == 'pl':
    nr  = "UA-16277394-17"
  else:
    nr = ""

  return nr

###############################################################################
def cera_home(request):

  # request POST/GET delivers all key/value pairs from URL (urldata is a dictionary) and generates an initial (bound) form
  if request.method == 'POST':
    urldata = request.POST.copy()
  elif request.method == 'GET':
    urldata = request.GET.copy()
  else:
    raise ValidationError(
      'request method %(method)s not supported',
      params = { 'method' : request.method }
    )

  cera = get_url_entry(urldata, 'cera', 'pub')

  if not cera in ['pub', 'st', 'dev', 'pr', 'pl'] and not request.user.is_authenticated:
    return redirect(reverse('login'))

  if not cera in ['pub', 'ng', 'nc', 'pr', 'ri', 'pl', 'st', 'dev', 'nc_ng']:
    raise ValidationError(
      'CERA site \'%(cera)s\' not supported.',
      params = { 'cera' : cera }
    )

  switched_to_pro = False
  if cera == 'pub' and request.user.is_authenticated:
    switched_to_pro = True
    cera = 'nc_ng'

  if has_url_entry(urldata, 'mapextent') or (has_url_entry(urldata, 'ne') and has_url_entry(urldata, 'sw')):
    mapextent = get_url_entry(urldata, 'mapextent', 'custom')
    if not EXTENTS.has_key(mapextent):
      raise ValidationError(
        'mapextent %(mapextent)s not supported',
        params = { 'mapextent' : mapextent }
      )
  else:
#   if cera == 'ng':
#     mapextent = '_gulf'
    if cera == 'pl':
      mapextent = 'parishes_la'
    else:
      mapextent = '_atlantic'

  urldata.setlist('ne', [ get_url_entry(urldata, 'ne', EXTENTS[mapextent][1]) ])
  urldata.setlist('sw', [ get_url_entry(urldata, 'sw', EXTENTS[mapextent][0]) ])

  ###########################
  form = CeraProForm(urldata)

  if not form.is_valid():
    raise ValidationError(
      'form validation failed: %(errors)s',
      params = { 'errors': str(form.errors)}
    )

  baseurl = expand_baseurl(cera)
  adminmode = get_adminmode()
  googlekey = getenv(CERA_ENV, 'GOOGLE_MAPS_KEY', '')

  # generate list of clean values (initial bound form)
  # with clean a) all key/value pairs that are not in the form get lost b) all initial values that are defined in forms.py get lost
  # function adds missing key/value pairs and initial values and builds all needed values:
  # a) url data that are known by the form are taken from the url
  # b) data that are not on the url but defined in the form dictionary below (CERA site specific) are taken from the dictionary
  # c) data that are not on the url and not in the dictionary but set as initial values in the form are taken from the form
  # a-c is handled by clean_data function (cases apply to form)
  # d) data that are on the url but not in the form are taken from the url (loop after the cleaned_data function)
  # e) data that are not on the url and not in the form are added by the render (html) function, like queryonoff

  # a) b) c)
  # CERA site specific initial values for the form are set here (no initial value in form.py)
  initial_values = form_dictionary(cera)
  if switched_to_pro:
    initial_values['cera'] = '!nc_ng'
  cleaned_data = form.clean(initial=initial_values)

  # add key/value pairs from url unknown to form (d)
  for k, v in urldata.dict().iteritems():
    if not cleaned_data.has_key(k):
      cleaned_data[k] = v

  # if this is not the first invocation
  if 'isdefault' in urldata:
    cleaned_data['isdefault'] = '0'
  if 'accept' in urldata:
    cleaned_data['accept'] = '1'

  values = []
  for k, v in cleaned_data.iteritems():
    values.append(v)

  ########
  dev_site = get_dev_site(cera)
  mapextent_data = set_mapextent_data(cera)
  analytics = analytics_nr(cera)

  if cera in ['pr', 'ri', 'pl', 'st', 'dev']:
    banner_asgs = cera
  else:
    banner_asgs = 'pro'

  ########
  return render(request, 'home/cera.html',
    {
      # form contains hidden input fields, id is set to key name
      'form': CeraProForm(cleaned_data, auto_id='%s'),

      # all other fields that are needed for data_array + config_data in html page

      # urldata/values is used to fill data_array in html file (<value>_check)
      'urldata': cleaned_data,
      'urldata_string': urllib.urlencode(cleaned_data, doseq=True),
      'values': values,
      # replace header tag in data_array
      'timestep': urldata.get('timestep', ''),

      # fields for config_data that are not already defined otherwise
      'debug': urldata.get('debug', 'off'),
      'queryonoff' : urldata.get('queryonoff', '0'),
      'maptype' : urldata.get('maptype', 'roadmap'),
      'anilayer': urldata.get('anilayer', ''),
      # data_url in config_data
      'banner_asgs' : banner_asgs,
      'dev_site' : dev_site,
      # Day/Storm tabs
      'selectmenu': urldata.get('selectmenu', '0'),
      'mapextent' : mapextent,
      'mapextent_data' : sorted(mapextent_data.iteritems()),
      'grid': urldata.get('grid', ''),
      'googlekey': googlekey,

      # all other values
      'baseurl' : baseurl,
      'basepath' : getenv(CERA_ENV, 'CERA_BASE_PATH', ''),      # cera website (htdocs) base directory ('cera' or 'cera_risk')
      'cgipath' : getenv(CERA_ENV, 'CERA_CGI_PATH', ''),        # cgi path (cgi-cera)
      'djangopath' : getenv(CERA_ENV, 'DJANGO_BASE_PATH', ''),  # django alias name as defined in conf ('cera-data' or 'cerarisk')
      'django_ceracgi' : getenv(CERA_ENV, 'DJANGO_CERACGI_PATH', ''),   # path to ceracgi for *.py scripts on wms_hosts (django alias name: only important for development website: use cera_data instead of cerarisk because cerarisk is not available on wms_hosts yet)
      'admin': adminmode,
      'query_source': QUERY_SOURCE,
      'wms_source': WMS_SOURCE,
      'ani_source': WMS_ANI_SOURCE,
      'analytics' : analytics,
      'is_authenticated' : request.user.is_authenticated,
      'userprofile' : request.user.userprofile.cera if request.user.is_authenticated else '',
      'user': request.user
    },
    content_type='text/html')

