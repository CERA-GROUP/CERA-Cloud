#!C:/Python27/python.exe -u
#
# Redirects WFS request to WFS_SERVER and returns received result to avoid WFS xml security 
# problems that occur when the wfs data are stored on a different domain related to the 
# google application
#
# Coastal Emergency Risks Assessment (CERA)	
# =============================================================================
# Copyright (c) 2006-2013 Carola Kaiser, Louisiana State University
# Distributed under the Boost Software License, Version 1.0. 
# See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# This is free software, but WITHOUT ANY WARRANTY; do not remove the copyright lines
 
import httplib
import os
import urlparse

from django.http import HttpResponse

WFS_SERVER = os.getenv("MAPSERVER_WMSHOST", "")

LOGFILENAME = 'c:/ms4w/Apache/logs/cera_wfs_forwarding.log'

#keys that need to be in upper case on the URL
UPPER_KEYS = [
    "SERVICE",
    "REQUEST",
    "VERSION",
    "NAMESPACE",
    "OUTPUTFORMAT",
    "RESULTTYPE",
    "PROPERTYNAME",
    "FEATUREVERSION",
    "MAXFEATURES",
    "EXPIRY",
    "SRSNAME",
    "BBOX",
    "FEATUREID",
    "FILTER",
    "SORTBY",
    "TRAVERSEXLINKDEPTH",
    "TRAVERSEXLINKEXPIRY",
    "PROPTRAVXLINKDEPTH",
    "PROPTRAVXLINKEXPIRY"
]

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

    query_string = {}

    for key in qs.keys():
        uc_key = key.upper()
        if not uc_key in UPPER_KEYS:
            query_string[key.lower()] = qs[key]
        else:
            query_string[uc_key] = qs[key]

    data = None
    format = ''
    try:
        for key in query_string.keys():
            if key == 'data_host' or key == 'legend':
                continue          # skip data_host and legend
            v = query_string[key]
            if (type(v) == type([])):
                for i in v:
                    url = "%s&%s=%s" % (url, key, i)
            else:
                url = "%s&%s=%s" % (url, key, v)

        data_host = get_dict_value(query_string, "data_host", WFS_SERVER)
        outputformat = get_dict_value(qs, "outputformat", "")

        if get_dict_value(query_string, "debug", "off") == "on":
            log = file(LOGFILENAME, "w+")
#            print >> log, "http://%s/cera_data/ceracgi/cera_wfs_cgi?%s" % (data_host, url)
            print >> log, "http://%s/cgi-cera/cera_wms.cgi?%s" % (data_host, url)
            log.close()
        
        # request the xml from the mapserver
        conn = httplib.HTTPConnection(data_host)
#        conn.request("GET", "/cera_data/ceracgi/cera_wfs_cgi?" + url)
        conn.request("GET", "/cgi-cera/cera_wms.cgi?" + url)
        r = conn.getresponse()
        if (r.status):
            data = r.read()
            if outputformat == 'geojson':
                format = 'application/json'
            else:
                format = 'text/xml'
        else:
            data = r.reason
            format = 'text/plain'
 
    except Exception, e:
        import traceback, sys
        data = "An error occurred: %s\n%s\n" % (
            str(e), "".join(traceback.format_tb(sys.exc_traceback)))
        format = 'text/plain'

    return HttpResponse(data, content_type=format)
