#!C:/Python27/python.exe -u
#
# CGI script launching the Mapserver/Google Maps based CERA web application
# =============================================================================
# Copyright (c) 2006-2016 Carola Kaiser, Louisiana State University
# Distributed under the Boost Software License, Version 1.0.
# See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# This is free software, but WITHOUT ANY WARRANTY; do not remove the copyright lines

################################################################################
# no need to change anything below this line

# import libraries
import os
import tempfile
import re
#import cgi
#import cgitb; cgitb.enable()

import urlparse
from django.http import HttpResponse
from cStringIO import StringIO

################################################################################
# class allowing to substitute multiple search strings at once
# the search strings are wrapped as %key%
class make_xlat:
    def __init__(self, *args, **kwds):
        self.adict = dict(*args, **kwds)
        self.rx = self.make_rx()
    def make_rx(self):
        return re.compile('%%%s%%' % '%|%'.join(map(re.escape, self.adict)))
    def one_xlat(self, match):
        def extract_key(m):
            return m[1:len(m)-1]
        return self.adict[extract_key(match.group(0))]
    def __call__(self, text):
        return self.rx.sub(self.one_xlat, text)

# same as above, except replaces [key] with values
class make_html_xlat:
    def __init__(self, *args, **kwds):
        self.adict = dict(*args, **kwds)
        self.rx = self.make_rx()
    def make_rx(self):
        return re.compile('\[%s\]' % '\]|\['.join(map(re.escape, self.adict)))
    def one_xlat(self, match):
        def extract_key(m):
            return m[1:len(m)-1]
        return self.adict[extract_key(match.group(0))]
    def __call__(self, text):
        return self.rx.sub(self.one_xlat, text)

# same as above, except replaces [<value>_check] with 'true'
class make_html_xlat_check:
    def __init__(self, *args, **kwds):
        self.adict = dict(*args, **kwds)
        self.rx = self.make_rx()
    def make_rx(self):
        return re.compile('\[%s_check\]' % '_check\]|\['.join(map(re.escape, self.adict)))
    def one_xlat(self, match):
        return "true"
    def __call__(self, text):
        return self.rx.sub(self.one_xlat, text)

# same as above, except replaces undefined [<value>_check] with 'false'
class make_html_xlat_undefined_check:
    def __init__(self):
        self.rx = self.make_rx()
    def make_rx(self):
        return re.compile('\[.*_check\]')
    def one_xlat(self, match):
        return "false"
    def __call__(self, text):
        return self.rx.sub(self.one_xlat, text)

# test if key is in list, e.g., to set initial [ne],[sw] mapextent
def key_in_list(key, l):
    for k, v in l:
        if (key == k):
            return True
    return False

# return value for key from list, e.g., to get the current mapextent
def value_from_list(key, l):
    for k, v in l:
        if (key == k):
            return v
    raise "Unknown key: " + key

# replace value for key in list, e.g., to put new wms_source back into list
def value_into_list(key, value, l):
    i = 0
    for k, v in l:
        if (key == k):
            l[i] = (key, value)
            return
        i = i + 1
    raise "Unknown key: " + key

# append key value pair if not in list, e.g. for [ne],[sw] mapextent
def append_value_if_not_in_list(key, value, list):
    if (key_in_list(key, list)):
        return
    list.append((key, value))

# append key, value from form to list
def append_pair(qs, key, value):
    if (type(value) == type([])):
        found = False
        for v in value:
            if (len(v) > 0):
                found = True
                qs.append((key, v))
        if (not found):
            return False
    elif (len(value) > 0):
        qs.append((key, value))
    else:
        return False
    return True

# append all form variables to the given list
def append_form_to_list(form, l):
    # copy pairs from the list if the key is not given in the form
    qs = []
    keys = form.keys()
    for qkey, qvalue in l:
#        print "qkey, qvalue:", qkey, qvalue, "<br>"
        if (qkey in keys):
            value = form[qkey]
            if (value == "default" or (not append_pair(qs, qkey, form[qkey]))):
                qs.append((qkey, qvalue))
        else:
            qs.append((qkey, qvalue))

    for key in keys:
        if (not key_in_list(key, l)):
            append_pair(qs, key, form[key])
    return qs

# generate the query string from the goven dictionary
def make_url_from_list(l):
    query_string = ""
    first = True
    for v in l:
        if (not first):
            query_string = query_string + "&"
        query_string = query_string + "%s=%s" % (v[0], v[1])
        first = False
    return query_string

# generate a new unique name
def generate_temp_name(prefix, template):
    tfile, name = tempfile.mkstemp(".map", prefix, os.path.split(template)[0])
    os.close(tfile)
    return name

# generate (k, v) pairs from the QS list
def pairwise(l):
    itnext = iter(l).next
    while True:
        v = itnext()
        yield v[0], v[1]

# generate (v, k) pairs from the QS list
def inv_pairwise(l):
    itnext = iter(l).next
    while True:
        v = itnext()
        yield v[1], v[0]

# returns the first key in a dictionary
def first_key(d):
    for k, v in d.iteritems():
        return k
    raise 'Empty dictionary'

###############################################################################
def static_var(varname, value):
    def decorate(func):
        setattr(func, varname, value)
        return func
    return decorate

from django.views.decorators.csrf import csrf_protect
from django.template.loader import engines
from django.template import RequestContext

def do_generate_html(request, QS, fs, template, extents, logfile):

    def get_dict_value(d, k, deflt = None):
        if k.lower() in d:
            return d[k.lower()][0]
        if k.upper() in d:
            return d[k.upper()][0]
        return deflt

    qs = append_form_to_list(fs, QS)

    mapextent = value_from_list('mapextent', qs)
    if (extents.has_key(mapextent) == False):
        mapextent = first_key(extents)

    # appends two key=value mapextent pairs on URL if pairs are not in list
    # (normally only on very first start)
    append_value_if_not_in_list("sw", extents[mapextent][0], qs)
    append_value_if_not_in_list("ne", extents[mapextent][1], qs)

    # write log
    if (get_dict_value(qs, 'debug', 'off') == 'on'):
        log = file(logfile, "a+")
        print >> log, make_url_from_list(qs)
        log.close()

    # generate the web page

    # translate all [key] tags in html with corresponding value (serverside)
    translate1 = make_html_xlat(dict(pairwise(qs)))

    # translate all [<value>_check] in html with "true"
    translate2 = make_html_xlat_check(dict(inv_pairwise(qs)))

    # translate all undefined [<...>_check] in html with "false"
    translate3 = make_html_xlat_undefined_check()

    result = StringIO()
    print >> result, translate3(translate2(translate1(template))),

    t = engines['django'].from_string(result.getvalue())
    result.close()

    c = RequestContext(request, {})
    response = HttpResponse(t.render(c), content_type='text/html')

    return response

###############################################################################
# here we do everything what needs to be done

adminmode = "0"
if (os.getenv("CERA_ADMINMODE", "0") != "0"):
    adminmode = "1"

#    tag         default value
QS = [
    ("day", ""),
    ("time", ""),
    ("com", ""),
    ("timestep", ""),
    ("year", ""),
    ("storm", ""),
    ("advisory", ""),
    ("track", ""),

    # see in django.wsgi for passing from http.conf
#    ("googlekey", os.environ.get("GOOGLEKEY","")),
    ("googlekey", os.getenv("GOOGLE_MAPS_KEY","")),
    ("maptype", "Roadmap"),
    ("maptools", "0"),
    # marks the webpage as very first page; after that it is always 0
    ("isdefault", "1"),
    ("is_storm", "0"),
    ("has_invest_or_subtrack", "0"),
    ("has_wvelf", "1"),
    # Day/Storm tabs
    ("selectmenu", "0"),

    ("admin", adminmode),
    ("anilayer", ""),
    ("grid",""),
    ("queryonoff", "false"),
    ("zoom", "")
]

from django.http import Http404

def do_generate_cera_html(request, template, extends, config_data, logfile):

    if request.method == 'GET':
        params = request.META['QUERY_STRING']
        qs = urlparse.parse_qs(params)
    elif request.method == 'POST':
        qs = request.POST
    else:
        raise Http404

#    foo
    return do_generate_html(request, config_data, qs, template, extends, logfile)


###############################################################################
# DEV/PRO page

EXTENTS_DEV = {
#   latlongSouthWest  latlongNorthEast
    "atlantic" : [ "14.0,-98", "45.0,-60" ],
    "nc" : [ "34.1,-78.8", "37.0,-75.4" ],
    "nj" : [ "38.78,-75.62", "42.77,-71.84" ],
    "va" : [ "36.49,-77.5", "39.84,-74.85" ],
    "gulf" : [ "21,-97", "37,-74" ],
    "la" : [ "28.5,-93.5", "31.5,-88.8" ],
    "orleans" : [ "29.81,-90.33", "30.08,-89.87" ],
    "ms" : [ "29.5,-89.7", "31.0,-88.5" ],
    "al" : [ "29.5,-88.5", "31.0,-87.5" ],
    "flw" : [ "24.7,-87.3", "30.9,-81.1" ],
    "ri" : [ "41.0, -72.5", "42.4, -70.0" ],
    "tampa" : [ "27.57,-82.85", "28.06,-82.38" ],
    "tx" : [ "26.5,-95.5", "30.0,-91.5" ],
    "houston" : [ "29.17,-95.56", "29.94,-94.68" ]

}

@csrf_protect
@static_var("template_data", None)
@static_var("config_data", None)
def do_generate_cera_html_dev(request):

    CFGFILEDIR = "C:/ms4w/Apache/cera_wms_data/"
    LOGFILE = CFGFILEDIR + "cera_cgi.log"

    WEBROOT = os.getenv("WEBROOT", "htdocs")
    TEMPLATE = "C:/ms4w/Apache/" + WEBROOT + "/cera/cera-pro.html"

    if do_generate_cera_html_dev.config_data is None:
        QS.append(("mapextent", "atlantic"))
        QS.append(("asgs", "pro"))
        QS.append(("tz", "utc"))
        do_generate_cera_html_dev.config_data = QS

    # open html template file
    if do_generate_cera_html_dev.template_data is None:
        file_template = file(TEMPLATE, "r")
        do_generate_cera_html_dev.template_data = file_template.read()
        file_template.close()

    return do_generate_cera_html(request, do_generate_cera_html_dev.template_data, \
        EXTENTS_DEV, do_generate_cera_html_dev.config_data, LOGFILE)

###############################################################################
# NC page

EXTENTS_NC = {
#                  latlongSouthWest  latlongNorthEast
    "atlantic" : [ "14.0,-98", "45.0,-60" ],
    "nc" : [ "34.1,-78.8", "37.0,-75.4" ],
    "nj" : [ "38.78,-75.62", "42.77,-71.84" ],
    "va" : [ "36.49,-77.5", "39.84,-74.85" ]
}

@csrf_protect
@static_var("template_data", None)
@static_var("config_data", None)
def do_generate_cera_html_nc(request):

    CFGFILEDIR = "C:/ms4w/Apache/cera_wms_data/"
    LOGFILE = CFGFILEDIR + "cera_nc_cgi.log"

    WEBROOT = os.getenv("WEBROOT", "htdocs")
    TEMPLATE = "C:/ms4w/Apache/" + WEBROOT + "/cera/cera_nc.html"

    if do_generate_cera_html_nc.config_data is None:
        QS.append(("mapextent", "atlantic"))
        QS.append(("asgs", "nc"))
        QS.append(("tz", "edt"))
        do_generate_cera_html_nc.config_data = QS

    # open html template file
    if do_generate_cera_html_nc.template_data is None:
        file_template = file(TEMPLATE, "r")
        do_generate_cera_html_nc.template_data = file_template.read()
        file_template.close()

    return do_generate_cera_html(request, do_generate_cera_html_nc.template_data, \
        EXTENTS_NC, do_generate_cera_html_nc.config_data, LOGFILE)

###############################################################################
# NG page

EXTENTS_NG = {
# latlongSouthWest  latlongNorthEast
    "gulf" : [ "21,-97", "37,-74" ],
    "la" : [ "28.5,-93.5", "31.5,-88.8" ],
    "orleans" : [ "29.81,-90.33", "30.08,-89.87" ],
    "ms" : [ "29.5,-89.7", "31.0,-88.5" ],
    "al" : [ "29.5,-88.5", "31.0,-87.5" ],
    "ng" : [ "28.5,-94.0", "30.5,-86.5" ]
}

@csrf_protect
@static_var("template_data", None)
@static_var("config_data", None)
def do_generate_cera_html_ng(request):

    CFGFILEDIR = "C:/ms4w/Apache/cera_wms_data/"
    LOGFILE = CFGFILEDIR + "cera_ng_cgi.log"

    WEBROOT = os.getenv("WEBROOT", "htdocs")
    TEMPLATE = "C:/ms4w/Apache/" + WEBROOT + "/cera/cera_ng.html"

    if do_generate_cera_html_ng.config_data is None:
        QS.append(("mapextent", "gulf"))
        QS.append(("asgs", "ng"))
        QS.append(("tz", "cdt"))
        do_generate_cera_html_ng.config_data = QS

    # open html template file
    if do_generate_cera_html_ng.template_data is None:
        file_template = file(TEMPLATE, "r")
        do_generate_cera_html_ng.template_data = file_template.read()
        file_template.close()

    return do_generate_cera_html(request, do_generate_cera_html_ng.template_data, \
        EXTENTS_NG, do_generate_cera_html_ng.config_data, LOGFILE)

###############################################################################
# RI page

EXTENTS_RI = {
# latlongSouthWest  latlongNorthEast
    "atlantic" : [ "14.0,-98", "45.0,-60" ],
    "ri" : [ "41.0, -72.5", "42.4, -70.0" ]
}

@csrf_protect
@static_var("template_data", None)
@static_var("config_data", None)
def do_generate_cera_html_ri(request):

    CFGFILEDIR = "C:/ms4w/Apache/cera_wms_data/"
    LOGFILE = CFGFILEDIR + "cera_ri_cgi.log"

    WEBROOT = os.getenv("WEBROOT", "htdocs")
    TEMPLATE = "C:/ms4w/Apache/" + WEBROOT + "/cera/cera_ri.html"

    if do_generate_cera_html_ri.config_data is None:
        QS.append(("mapextent", "gulf"))
        QS.append(("asgs", "ri"))
        QS.append(("tz", "cdt"))
        do_generate_cera_html_ri.config_data = QS

    # open html template file
    if do_generate_cera_html_ri.template_data is None:
        file_template = file(TEMPLATE, "r")
        do_generate_cera_html_ri.template_data = file_template.read()
        file_template.close()

    return do_generate_cera_html(request, do_generate_cera_html_ri.template_data, \
        EXTENTS_RI, do_generate_cera_html_ri.config_data, LOGFILE)
