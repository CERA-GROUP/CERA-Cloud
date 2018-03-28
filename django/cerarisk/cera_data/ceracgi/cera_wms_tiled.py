# Coastal Emergency Risks Assessment (CERA)	 
# ===================================================================================
# Copyright (c) 2006-2013, Louisiana State University
# Distributed under the Boost Software License, Version 1.0. 
# See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# This is free software, but WITHOUT ANY WARRANTY; do not remove the copyright lines  

import os
import wms_tilecache
import urlparse

CFGFILEDIR = "C:/ms4w/Apache/cera_wms_data/"
CFGFILE = CFGFILEDIR + "cera_wms.cfg"
LOGFILE = "C:/ms4w/Apache/logs/cera_wms_tiled.log"
WMSHOST = os.getenv("MAPSERVER_WMSHOST", "")

# everything besides "false", "no", "off", or "0" will be interpreted as 'yes'
QS = [
    ("debug", "off"),
    ("wms_host", "http://%s" % WMSHOST),
    ("wms_dir", CFGFILEDIR),
    ("cache_dir_web", "C:/ms4w/Apache/cera_wms_data/tilecache"),
    ("cache_only", "no"),
    ("metatile", "no"),
    ("metasize", "1,1"),
    ("metatileexact", "no")
]

#keys that need to be in upper case on the URL
UPPER_KEYS = [
    "SERVICE",
    "REQUEST",
    "VERSION",
    "LAYERS",
    "STYLES",
    "FORMAT",
    "TRANSPARENT",
    "HEIGHT",
    "WIDTH",
    "REASPECT",
    "BGCOLOR",
    "SRS",
    "BBOX"
]

# main entry point called by django
def do_work(request, filename = 'cera_wms_tiled'):
    # parse query string
    qs = urlparse.parse_qs(request.META['QUERY_STRING'])

    query_string = {}

    for key in qs.keys():
        uc_key = key.upper()
        if not uc_key in UPPER_KEYS:
            query_string[key.lower()] = qs[key]
        else:
            query_string[uc_key] = qs[key]

#    logout = file(LOGFILE, "a+")
#    print >> logout, query_string
#    logout.close()

    # retrieve other variable from http environment
    path_info = request.META['PATH_INFO']
    host = "http://" + request.META['HTTP_HOST'] + request.META['SCRIPT_NAME'] + request.META['PATH_INFO']
    req_method = request.META['REQUEST_METHOD']

    return wms_tilecache.do_work(QS, query_string, CFGFILE, LOGFILE, path_info, host, req_method, request)

