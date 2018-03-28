#!C:/Python27/python.exe -u
#
# Redirects requests to server and returns received result to avoid cross 
# domain security problems that occur when the data are stored on a different 
# domain related to the google application
#
# Coastal Emergency Risks Assessment (CERA)	
# =============================================================================
# Copyright (c) 2006-2013 Carola Kaiser, Louisiana State University
# Distributed under the Boost Software License, Version 1.0. 
# See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# This is free software, but WITHOUT ANY WARRANTY; do not remove the copyright lines
 
import httplib
import os
import datetime
import pytz
import urlparse

from django.http import HttpResponse

CERA_DATA_SERVER = os.getenv("MAPSERVER_WMSHOST", "")

###############################################################################
# get pytz timezone from descriptive short name
def get_pytz_timezone(tz):

    tz = tz.upper()
    if tz == 'CDT' or tz == 'CST':
        return pytz.timezone('US/Central')

    if tz == 'EDT' or tz == 'EST':
        return pytz.timezone('US/Eastern')

    if tz == 'AST':
        return pytz.timezone('America/Puerto_Rico')

    return pytz.utc

def as_timezone(dt, tz):
     dt = dt.astimezone(tz)
     return tz.normalize(dt)

###############################################################################
def do_work(request):

    def get_dict_value(d, k, deflt = None):
        if k.lower() in d:
            return d[k.lower()][0]
        if k.upper() in d:
            return d[k.upper()][0]
        return deflt

    # extract the url
    url = ""
    qs = urlparse.parse_qs(request.META['QUERY_STRING'])

    data = None
    format = ''
    try:
        # split WMS keys
        day = get_dict_value(qs, "day")
        time = get_dict_value(qs, "time")
        data_host = get_dict_value(qs, "data_host", CERA_DATA_SERVER)

        dt = datetime.datetime.strptime(day, "%Y%m%d")
        t = datetime.datetime.strptime(time, "%H%M") 
        dt = dt + datetime.timedelta(seconds=t.hour*3600+t.minute*60)

        tz = get_pytz_timezone(get_dict_value(qs, 'tz', 'utc'))
        dt = as_timezone(tz.localize(dt), pytz.utc)

        y = dt.strftime("%Y")
        m = dt.strftime("%m")
        d = dt.strftime("%d")
        h = dt.strftime("%H")

        com = get_dict_value(qs, "com")
        l = get_dict_value(qs, "layer")

        # request the json from the ANIDATA_SERVER
        conn = httplib.HTTPConnection(data_host)
        conn.request("GET", "/cera_wms_data/%s/%s/%s/%s/%s/%s/%s.json" % (y, m, d, h, com, l, l))
        r = conn.getresponse()
        if (r.status):
            data = r.read()
            format = 'text/json'
        else:
            data = r.reason
            format = 'text/plain'
 
    except Exception, e:
        import traceback, sys
        data = "An error occurred: %s\n%s\n" % (
            str(e), "".join(traceback.format_tb(sys.exc_traceback)))
        format = 'text/plain'

    return HttpResponse(data, content_type=format)

