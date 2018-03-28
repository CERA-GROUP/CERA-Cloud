#!C:/Python27/python.exe -u
# Copyright(c) 2006-2016 Carola Kaiser (ckaiser <at> cct.lsu.edu)
# Distributed under the Boost Software License, Version 1.0. 
# See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
#
# CGI script launching the Mapserver/Google Maps based Particle Movement web application

################################################################################
# no need to change anything below this line

# import libraries
import os
import subprocess
import tempfile
import re
import datetime
import pytz
import mapscript 

from cStringIO import StringIO
from django.http import HttpResponse

# Exceptions as used in this file
class Error(Exception):
    pass
    
class KeyError(Error):
    def _get_message(self, message): 
        return self._message
    def _set_message(self, message): 
        self._message = message
    message = property(_get_message, _set_message)

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

###############################################################################
# test if key is in list
def key_in_list(key, l):
    for k, v in l:
        if (key.lower() == k.lower()):
            return True
    return False

# return value for key from list
def value_from_list(key, l, default_val = None):
    for k, v in l:
        if (key.lower() == k.lower()):
            return v
    if (default_val is None):
        raise KeyError("Unknown key: " + key)
    return default_val

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

# replace given value if key exists, otherwise append
def replace_pair(l, key, value):
    for i, p in enumerate(l):
        if (key == p[0]):
            l = l[0:i] + l[i+1:]
            break

    l.append((key, value))
    return l

# append all form variables to the given list
def append_form_to_list(form, l):
    # copy pairs from the list if the key is not given in the form
    qs = []
    keys = form.keys()
    for qkey, qvalue in l:
#        print "qkey, qvalue:", qkey, qvalue, "<br>"
        if (qkey in keys):
            value = form[qkey]
            if (not append_pair(qs, qkey, form[qkey])):
                qs.append((qkey, qvalue))
        else:
            qs.append((qkey, qvalue))

    for key in keys:
        if (not key_in_list(key, l)):
            append_pair(qs, key, form[key])
    return qs

# generate the query string from the given dictionary
def make_url_from_list(l):
    query_string = ""
    first = True
    for v in l:
        if (not first):
            query_string = query_string + "&"
        query_string = query_string + "%s=%s" % (v[0], v[1])
        first = False
    return query_string

# generate (k, v) pairs from the QS list
def pairwise(l):
    itnext = iter(l).next
    while True:
        v = itnext()
        yield v[0], v[1]
        
# use mapscript to render the requested WFS data
def render_with_mapserver(qs, mapfilename):

    req = mapscript.OWSRequest() 
    for k, v in qs:
        req.setParameter(k.upper(), v)

    wfs = mapscript.mapObj(mapfilename)

    mapscript.msIO_installStdoutToBuffer()
    wfs.OWSDispatch(req)

    format = mapscript.msIO_stripStdoutBufferContentType()
    if format == 'vnd.ogc.se_xml':
        format = 'text/xml'

    content = mapscript.msIO_getStdoutBufferString()
    mapscript.msIO_resetHandlers()

    return content, format

###########################################################
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

# generate a new unique name
def generate_temp_name(prefix, template):
    tfile, name = tempfile.mkstemp(".map", prefix, os.path.split(template)[0])
    return name, tfile

# generate the mapfile from the template
def generate_mapfile(tmplfile, outfile, cgivars):

    tmplfile.seek(0)

    # handle mapfile
    translate = make_xlat(dict(pairwise(cgivars)))
    for line in tmplfile:
        print >> outfile, translate(line),

    # make sure file is closed
    outfile.close()

###########################################################
# here we do everything what needs to be done
def static_var(varname, value):
    def decorate(func):
        setattr(func, varname, value)
        return func
    return decorate

@static_var("map_filename", None)
@static_var("map_data", None)
def do_work(request, QS, fs, MAPFILEDIR, MAPFILE, MAPSERV):

    return HttpResponse('foo', content_type='text/plain')

    def get_dict_value(d, k, deflt = None):
        if k.lower() in d:
            return d[k.lower()][0]
        if k.upper() in d:
            return d[k.upper()][0]
        return deflt

    data = None
    format = ''

    try:
        if do_work.map_data is None:
            do_work.map_filename = os.path.join(MAPFILEDIR, MAPFILE)
            map_file = file(do_work.map_filename, "r")
            do_work.map_data = map_file.read()
            map_file.close()

        qs = append_form_to_list(fs, QS)

        # convert given WMS tags on URL to requested tags in mapfile and cfg file
        # URL:day=YYYYMMDD&time=HHMM..  - mapfile: year/month/day/hour/..
        day = get_dict_value(fs, "day")
        dt = datetime.datetime.strptime(day, "%Y%m%d")

        time = get_dict_value(fs, "time")
        t = datetime.datetime.strptime(time, "%H%M") 

        dt = dt + datetime.timedelta(seconds=t.hour*3600+t.minute*60)

        tz = get_pytz_timezone(get_dict_value(fs, 'tz', 'utc'))
        dt = as_timezone(tz.localize(dt), pytz.utc)

        qs = replace_pair(qs, "year", dt.strftime("%Y"))
        qs = replace_pair(qs, "month", dt.strftime("%m"))
        qs = replace_pair(qs, "day", dt.strftime("%d"))
        qs = replace_pair(qs, "time", dt.strftime("%H"))
        qs = replace_pair(qs, "tz", "utc")

        # process mapfile
        mapfilename, mapfile = generate_temp_name("mapfile", do_work.map_filename)
        generate_mapfile(do_work.map_data, mapfile, qs)
    
        # call the Mapserver, intercept output and forward back to client
        if get_dict_value(fs, 'request', 'GetFeature') == 'GetFeature':
            data, format = render_with_mapserver(qs, mapfilename)
            qs.append(("map", mapfilename))

            if len(data) == 0:
                data = 'no data returned from mapserver'
                format = 'text/plain'

        else:
            # for all non-GetMap requests call the Mapserver directly, 
            # intercept output and forward back to client
            qs.append(("map", mapfilename))

            os.putenv("QUERY_STRING", make_url_from_list(qs))
            p = subprocess.Popen(MAPSERV, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (stdout, stderr) = p.communicate()

            # log error output from mapserver (if any)
            if len(stderr) > 0:
                data = stderr
            else:
                data = stdout

            format = 'text/plain'

    except Exception, e:
        import traceback, sys
        data = "An error occurred: %s\n%s\n" % (
            str(e), "".join(traceback.format_tb(sys.exc_traceback)))
        format = 'text/plain'

    os.remove(mapfilename)        # remove the temporary (generated) mapfile

    # write log, if debug is enabled
    if get_dict_value(fs, 'debug', 'off') == 'on':
        log = file("cera_wfs.log", "a+")
        print >> log, make_url_from_list(qs)
        log.close()

    return HttpResponse(data, content_type=format)
    
