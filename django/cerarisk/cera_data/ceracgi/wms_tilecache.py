#!C:\Python27\python.exe
# script to create missing CERA tile cache images which have not been pre-rendered

# Copyright Carola Kaiser 2006-2015, Louisiana State University
# Distributed under the Boost Software License, Version 1.0.
# See accompanying file LICENSE_1_0.txt or copy at
# http://www.boost.org/LICENSE_1_0.txt)

from CeraCache import Service, Layer, Tile, genericHandler, cfgfiles, TileCacheException
from CeraCache.Service import binaryPrint

import os, sys, traceback
import re
import tempfile
import datetime
import _strptime
import pytz
from cStringIO import StringIO
import urllib2

from django.shortcuts import render_to_response
from django.http import HttpResponse

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

###############################################################################
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

# generate a new unique name
def generate_temp_name(prefix, template):
    tfile, name = tempfile.mkstemp(".cfg", prefix, os.path.split(template)[0])
    os.close(tfile)
    return name

# generate (k, v) pairs from the forms parameters
def pairwise(l):
    itnext = iter(l).next
    while True:
        v = itnext()
        yield v[0], v[1]

###############################################################################
def expand_configdata(configdata, cgivars):

    # create temporary output file
    infile = StringIO(configdata)
    outfile = StringIO()

    # handle mapfile
    translate = make_xlat(dict(pairwise(cgivars)))
    for line in infile:
        print >> outfile, translate(line),

    outfile.seek(0)
    return outfile

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
# main entry point
def static_var(varname, value):
    def decorate(func):
        setattr(func, varname, value)
        return func
    return decorate

@static_var("config_filename", None)
@static_var("config_data", None)
def do_work(QS, fs, cfgfile, logfile, path_info, host, req_method, request):

    def get_dict_value(d, k, deflt = None):
        if k.lower() in d:
            return d[k.lower()][0]
        if k.upper() in d:
            return d[k.upper()][0]
        return deflt


    if do_work.config_data is None:
        workingdir = os.path.abspath(os.path.join(os.getcwd(), os.path.dirname(sys.argv[0])))
        do_work.config_filename = os.path.join(workingdir, cfgfile)
        config_file = file(do_work.config_filename, "r")
        do_work.config_data = config_file.read()

    data = 'no error'
    format = 'text/plain'
    svc = None

    try:
        qs = append_form_to_list(fs, QS)

        # split WMS keys
        day = get_dict_value(fs, "day")
        time = get_dict_value(fs, "time")

        dt = datetime.datetime.strptime(day, "%Y%m%d")
        t = datetime.datetime.strptime(time, "%H%M")
        dt = dt + datetime.timedelta(seconds=t.hour*3600+t.minute*60)

        tz = get_pytz_timezone(get_dict_value(fs, 'tz', 'utc'))
        dt = as_timezone(tz.localize(dt), pytz.utc)

        qs = replace_pair(qs, "y", dt.strftime("%Y"))
        qs = replace_pair(qs, "m", dt.strftime("%m"))
        qs = replace_pair(qs, "d", dt.strftime("%d"))
        qs = replace_pair(qs, "t", dt.strftime("%H"))
        qs = replace_pair(qs, "tz", "utc")

        cfgfilep = expand_configdata(do_work.config_data, qs)

        if get_dict_value(fs, 'debug', 'off') == 'on':
            logout = file(logfile, "a+")
            for line in cfgfilep:
                print >> logout, line,
            logout.close()
            cfgfilep.seek(0)

        svc = Service.loadfp(cfgfilep, do_work.config_filename)
        data, format = genericHandler(svc, dict(qs), path_info, host, req_method)

#        from django.shortcuts import render_to_response
#        return render_to_response('test.html', { 'params': request, 'config': do_work.config_data, 'format': format })

        cfgfilep = None

    except Exception, e:
        if 1: #get_dict_value(fs, 'debug', 'off') == 'on':
            logout = file(logfile, "a+")
            data = "An error occurred: %s, %s\n%s\n%s\nday='%s'\n" % (
                str(e), type(e), qs, "".join(traceback.format_tb(sys.exc_traceback)), day)
            print >> logout, data
            logout.close()
        del svc     # make sure files are properly closed

        from django.http import Http404
        raise Http404
    
    del svc     # make sure files are properly closed

    response = HttpResponse(data, content_type=format)
    if format == 'application/vnd.google-earth.kml+xml':
        response['Content-Disposition'] = 'attachment; filename=cera.kml'

    return response

###############################################################################
# main entry point for animation
def get_level(layer, width, bbox):

    num_tiles = (width + 255) / 256
    for z in range(1, 20):
        bottomleft = layer.getClosestCell(z, bbox[0:2])
        topright   = layer.getClosestCell(z, bbox[2:4])
        delta = topright[0] - bottomleft[0]
        if (delta+1 == num_tiles or delta == num_tiles):
            return z

    raise Exception("Couldn't retrieve resolution level\n")

def set_params_entry(d, k, v):
    if (d.has_key(k.lower())):
        d[k.lower()] = v
    else:
        d[k.upper()] = v

def write_png(name, img):
    try:
        import cStringIO as StringIO
    except ImportError:
        import StringIO

    buffer = StringIO.StringIO()
    img.save(buffer, "PNG", optimize=1)
    buffer.seek(0)

    f = file(name, "w+")
    try:
        import msvcrt
        msvcrt.setmode(f.fileno(), os.O_BINARY)
    except:
        pass

    f.write(buffer.read())
    f.close()

###############################################################################
def LatLonToPixel(lat, lon, z, size):
    mx, my = Layer.LatLonToMeters(lat, lon)
    return Layer.MetersToPixels(mx, my, z, size)

###############################################################################
@static_var("config_filename", None)
@static_var("config_data", None)
def do_animation_work(QS, fs, cfgfile, logfile, path_info, host, req_method):

    def get_dict_value(d, k, deflt = None):
        if k.lower() in d:
            return d[k.lower()][0]
        if k.upper() in d:
            return d[k.upper()][0]
        return deflt


    if do_work.config_data is None:
        workingdir = os.path.abspath(os.path.join(os.getcwd(), os.path.dirname(sys.argv[0])))
        do_work.config_filename = os.path.join(workingdir, cfgfile)
        config_file = file(do_work.config_filename, "r")
        do_work.config_data = config_file.read()

    svc = None
    data = None

    try:
        qs = append_form_to_list(fs, QS)

        debug = value_from_list("debug", qs) not in ("false", "off", "no", "disable")
#        debug = True
#        if debug:
        log = file(logfile, "a+")

        # split WMS keys
        day = get_dict_value(fs, "day")
        time = get_dict_value(fs, "time")

        dt = datetime.datetime.strptime(day, "%Y%m%d")
        t = datetime.datetime.strptime(time, "%H%M")
        dt = dt + datetime.timedelta(seconds=t.hour*3600+t.minute*60)

        tz = get_pytz_timezone(get_dict_value(fs, 'tz', 'utc'))
        dt = as_timezone(tz.localize(dt), pytz.utc)

        qs = replace_pair(qs, "y", dt.strftime("%Y"))
        qs = replace_pair(qs, "m", dt.strftime("%m"))
        qs = replace_pair(qs, "d", dt.strftime("%d"))
        qs = replace_pair(qs, "t", dt.strftime("%H"))
        qs = replace_pair(qs, "tz", "utc")

        if debug:
            print >> log, "-----------------------"
            print >> log, qs

        cfgfilep = expand_configdata(do_work.config_data, qs)

        svc = Service.loadfp(cfgfilep, do_work.config_filename)

        # figure out level
        bbox = map(float, value_from_list("BBOX", qs).split(','))
        width = int(value_from_list("WIDTH", qs))
        height = int(value_from_list("HEIGHT", qs))

        layer = svc.layers[svc.layers.keys()[0]]

        z = layer.getClosestLevel(layer.getResolution(bbox, (width, height)))
        bottomleft = layer.getClosestCell(z, (bbox[0], bbox[1]))
        topright   = layer.getClosestCell(z, (bbox[2], bbox[3]))

        if debug:
            print >> log, z, bottomleft, topright

        params = dict(pairwise(qs))
        set_params_entry(params, 'width', 256)
        set_params_entry(params, 'height', 256)
        params['opacity'] = 1.0

        if debug:
            print >> log, "-----------------------"
            print >> log, params

        try:
            import PIL.Image as Image
        except ImportError:
            raise Exception("Combining multiple layers requires Python Imaging Library.")

        try:
            import cStringIO as StringIO
        except ImportError:
            import StringIO

        start_x = bottomleft[0]
        start_y = bottomleft[1]
        end_x = topright[0]
        end_y = topright[1]

        size = ((end_x-start_x+1) * 256, (end_y-start_y+1) * 256)

        ul_bounds = Layer.TileLatLonBounds(start_x, end_y, z, 256)
        lr_bounds =  Layer.TileLatLonBounds(end_x+1, start_y-1, z, 256)

#        if debug:
#            print >> log, "ul_bounds: %s" % str(ul_bounds)

        ul_merc_x, ul_merc_y = LatLonToPixel(ul_bounds[2], ul_bounds[1], z, 256)
        lr_merc_x, lr_merc_y = LatLonToPixel(lr_bounds[2], lr_bounds[1], z, 256)
        ul_bbox_merc_x, ul_bbox_merc_y = LatLonToPixel(bbox[3], bbox[0], z, 256)
        lr_bbox_merc_x, lr_bbox_merc_y = LatLonToPixel(bbox[1], bbox[2], z, 256)

        if debug:
            print >> log, "ul_merc_x, ul_merc_y: %d,%d" % (ul_merc_x, ul_merc_y)
            print >> log, "lr_merc_x, lr_merc_y: %d,%d" % (lr_merc_x, lr_merc_y)
            print >> log, "ul_bbox_merc_x, ul_bbox_merc_y: %d,%d" % (ul_bbox_merc_x, ul_bbox_merc_y)
            print >> log, "lr_bbox_merc_x, lr_bbox_merc_y: %d,%d" % (lr_bbox_merc_x, lr_bbox_merc_y)

#        pixel_size_x = (lr_bounds[1]-ul_bounds[1])/size[0]
#        pixel_size_y = (ul_bounds[2]-lr_bounds[2])/size[1]

#        ul_x = int((bbox[0]-ul_bounds[1])/pixel_size_x)
#        ul_y = int((ul_bounds[2]-bbox[3])/pixel_size_y)

        ul_x = int(ul_bbox_merc_x - ul_merc_x)
        ul_y = int(ul_merc_y - ul_bbox_merc_y)

        if debug:
            print >> log, "bbox: %s" % str(bbox)
            print >> log, "size: %s" % str(size)
#            print >> log, "pixelsize: (%f,%f)" % (pixel_size_x, pixel_size_y)
            print >> log, "ul: (%d,%d)" % (ul_x, ul_y)

        result = Image.new("RGBA", size, None)
        format = "image/png"

        for x in range(start_x, end_x + 1):
            for y in range(end_y, start_y - 1, -1):
                bounds = Layer.TileLatLonBounds(x, y, z, 256)
                box = (bounds[1], bounds[0], bounds[3], bounds[2])

                if debug:
                    print >> log, "tile: %d, %d, %d" % (x, y, z)
                    print >> log, "bounds: %s" % str(box)

                set_params_entry(params, 'bbox', ','.join(map(str, box)))
                try:
                    xmin = (x-start_x)*256
                    ymin = (end_y-y)*256

                    if debug:
                        print >> log, "x, y, xmin, ymin: (%d,%d) (%d,%d)" % (x-start_x, end_y-y, xmin, ymin)

                    (format, data) = svc.dispatchRequest(params)
                    if (not format.startswith("image/")):
                        raise Exception("Coudn't render tile (bbox: %s)" % ','.join(map(str, box)))

                    image = Image.open(StringIO.StringIO(data))
#                    write_png("image%d%d.png" % (x, y), image)

                    result.paste(image, (xmin, ymin))

                except Exception, e:
                    if debug:
                        print >> log, "failed to retrieve tile: %s" % str(e)

        # crop image to the requested size
#        write_png("result.png", result)
        if debug:
            print >> log, "ul_x, ul_y, ul_x+width, ul_y+height: (%d,%d) (%d,%d)" % (ul_x, ul_y, ul_x+width, ul_y+height)

        result = result.crop((ul_x, ul_y, ul_x+width, ul_y+height))

        buffer = StringIO.StringIO()
        result.save(buffer, "PNG", optimize=1)
        buffer.seek(0)
        data = buffer.read()

    except Exception, e:
        if get_dict_value(fs, 'debug', 'off') == 'on':
            logout = file(logfile, "w+")
            data = "An error occurred: %s\n%s\n" % (
                str(e), "".join(traceback.format_tb(sys.exc_traceback)))
            print >> logout, data
            logout.close()

        del svc     # make sure files are properly closed

        from django.http import Http404
        raise Http404

    del svc     # make sure all files are properly closed

    return HttpResponse(data, content_type=format)

