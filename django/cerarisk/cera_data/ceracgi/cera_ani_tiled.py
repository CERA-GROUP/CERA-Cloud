#!C:/Python27/python.exe -u
#
# Coastal Emergency Risks Assessment (CERA)	
# =============================================================================
# Copyright(c) 2006-2015 Carola Kaiser (ckaiser <at> cct.lsu.edu)
# Distributed under the Boost Software License, Version 1.0. 
# See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)

import os
import wms_tilecache
import urlparse

CFGFILEDIR = "C:/ms4w/Apache/cera_wms_data/"
CFGFILE = CFGFILEDIR + "cera_wms.cfg"
LOGFILE = "C:/ms4w/Apache/logs/cera_wms_ani.log"
WMSHOST = os.getenv("MAPSERVER_WMSHOST", "")

QS = [
    ("debug", "off"),
    ("wms_host", "http://%s" % WMSHOST),
    ("wms_dir", CFGFILEDIR),
    ("cache_dir_web", "C:/ms4w/Apache/cera_wms_data/tilecache"),
    ("cache_only", "off"),
    # parameters will be used to read the created cache images but will be overwritten by tilecache_seed.py to create the 'timesteps' layer (and only for those)  
    ("metatile", "no"),
    ("metasize", "1,1"),
    ("metatileexact", "no")
]

# do main work
def do_work(request):
    # parse query string
    params = request.META['QUERY_STRING']
    qs = urlparse.parse_qs(params)

    # retrieve other variable from environment
    path_info = request.META['PATH_INFO']
    host = "http://" + request.META['HTTP_HOST'] + request.META['SCRIPT_NAME'] + request.META['PATH_INFO']
    req_method = request.META['REQUEST_METHOD']

    return wms_tilecache.do_animation_work(QS, qs, CFGFILE, LOGFILE, path_info, host, req_method)

