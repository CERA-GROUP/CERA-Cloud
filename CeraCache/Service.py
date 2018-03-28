#!/usr/bin/python

# BSD Licensed, Copyright (c) 2006-2008 MetaCarta, Inc.

class TileCacheException(Exception): pass

import sys, cgi, time, os, traceback, ConfigParser
import Cache, Caches
import Layer, Layers
import urllib2

# protecting against IncompleteRead errors from http sources
import httplib
def patch_http_response_read(func):
    def inner(*args):
        try:
            return func(*args)
        except httplib.IncompleteRead, e:
            return e.partial

    return inner

httplib.HTTPResponse.read = patch_http_response_read(httplib.HTTPResponse.read)

# Windows doesn't always do the 'working directory' check correctly.
if sys.platform == 'win32':
    workingdir = os.path.abspath(os.path.join(os.getcwd(), os.path.dirname(sys.argv[0])))
    cfgfiles = (os.path.join(workingdir, "tilecache.cfg"), os.path.join(workingdir,"..","tilecache.cfg"))
else:
    cfgfiles = ("/etc/tilecache.cfg", os.path.join("..", "tilecache.cfg"), "tilecache.cfg")

# this is taken from emails.utils which doesn't exist in IronPython yet
def formatdate(timeval=None, localtime=False, usegmt=False):
    """Returns a date string as specified by RFC 2822, e.g.:

    Fri, 09 Nov 2001 01:08:47 -0000

    Optional timeval if given is a floating point time value as accepted by
    gmtime() and localtime(), otherwise the current time is used.

    Optional localtime is a flag that when True, interprets timeval, and
    returns a date relative to the local timezone instead of UTC, properly
    taking daylight savings time into account.

    Optional argument usegmt means that the timezone is written out as
    an ascii string, not numeric one (so "GMT" instead of "+0000"). This
    is needed for HTTP, and is only used when localtime==False.
    """
    # Note: we cannot use strftime() because that honors the locale and RFC
    # 2822 requires that day and month names be the English abbreviations.
    if timeval is None:
        timeval = time.time()
    if localtime:
        now = time.localtime(timeval)
        # Calculate timezone offset, based on whether the local zone has
        # daylight savings time, and whether DST is in effect.
        if time.daylight and now[-1]:
            offset = time.altzone
        else:
            offset = time.timezone
        hours, minutes = divmod(abs(offset), 3600)
        # Remember offset is in seconds west of UTC, but the timezone is in
        # minutes east of UTC, so the signs differ.
        if offset > 0:
            sign = '-'
        else:
            sign = '+'
        zone = '%s%02d%02d' % (sign, hours, minutes // 60)
    else:
        now = time.gmtime(timeval)
        # Timezone offset is always -0000
        if usegmt:
            zone = 'GMT'
        else:
            zone = '-0000'
    return '%s, %02d %s %04d %02d:%02d:%02d %s' % (
        ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][now[6]],
        now[2],
        ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][now[1] - 1],
        now[0], now[3], now[4], now[5],
        zone)

class Capabilities (object):
    def __init__ (self, format, data):
        self.format = format
        self.data   = data

class Request (object):
    def __init__ (self, service):
        self.service = service
    def getLayer(self, layername):
        try:
            return self.service.layers[layername]
        except:
            raise TileCacheException("The requested layer (%s) does not exist. Available layers are: \n * %s" % (layername, "\n * ".join(self.service.layers.keys())))


def import_module(name):
    """Helper module to import any module based on a name, and return the module."""
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

# make this layer transparent using the given opacity
def apply_opacity(t, image, opacity):

    if t.layer.debug:
        sys.stderr.write(
            "Opacity: %.2f, layer: %s, tile: x: %s, y: %s, z: %s\n" % (
                opacity, t.layer.name, t.x, t.y, t.z) )

    try:
        import PIL.Image as Image
    except ImportError, E:
        raise Exception("Combining multiple layers requires Python Imaging Library.\n(Error was: %s)\n(Backtrace was: %s)" % (
            E, "".join(traceback.format_tb(sys.exc_info()[2]))
        ))

#    import PIL.ImageEnhance as ImageEnhance
    transparentimage = Image.new('RGBA', t.size(), (0, 0, 0, 0))
    transparentimage.paste(image, (0, 0), image)

    alpha = transparentimage.split()[3]
#    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    alpha = Image.eval(alpha, lambda x: x * opacity)
    transparentimage.putalpha(alpha)
    return transparentimage

class Service (object):
    __slots__ = ("layers", "cache", "metadata", "tilecache_options", "config", "files")

    def __init__ (self, cache, layers, metadata = {}):
        self.cache    = cache
        self.layers   = layers
        self.metadata = metadata

    def _loadFromSection (cls, config, section, module, **objargs):
        type  = config.get(section, "type")
        for opt in config.options(section):
            if opt not in ["type", "module"]:
                objargs[opt] = config.get(section, opt)

        object_module = None

        if config.has_option(section, "module"):
            object_module = import_module(config.get(section, "module"))
        else:
            if module is Layer:
                type = type.replace("Layer", "")
                object_module = import_module("CeraCache.Layers.%s" % type)
            else:
                type = type.replace("Cache", "")
                object_module = import_module("CeraCache.Caches.%s" % type)
        if object_module == None:
            raise TileCacheException("Attempt to load %s failed." % type)

        section_object = getattr(object_module, type)

        if module is Layer:
            return section_object(section, **objargs)
        else:
            return section_object(**objargs)
    loadFromSection = classmethod(_loadFromSection)

    def _load (cls, *files):
        cache = None
        metadata = {}
        layers = {}
        config = None
        debug = False
        try:
            config = ConfigParser.ConfigParser()
            config.read(files)

            if config.has_section("metadata"):
                for key in config.options("metadata"):
                    metadata[key] = config.get("metadata", key)

            if config.has_section("tilecache_options"):
                if 'path' in config.options("tilecache_options"):
                    for path in config.get("tilecache_options", "path").split(","):
                        sys.path.insert(0, path)
                if 'debug' in config.options("tilecache_options"):
                    debug = config.get("tilecache_options", "debug") not in ("false", "off", "no", "0")

            cache = cls.loadFromSection(config, "cache", Cache)

            layers = {}
            for section in config.sections():
                if section in cls.__slots__: continue
                try:
                    layers[section] = cls.loadFromSection(
                                        config, section, Layer,
                                        cache = cache)
                except Exception, E:
                    if debug:
                        print str(E)
                        print "".join(traceback.format_tb(sys.exc_info()[2]))

        except Exception, E:
            metadata['exception'] = E
            metadata['traceback'] = "".join(traceback.format_tb(sys.exc_info()[2]))
            if debug:
                print str(E)
                print "".join(traceback.format_tb(sys.exc_info()[2]))

        service = cls(cache, layers, metadata)
        service.files = files
        service.config = config
        return service

    load = classmethod(_load)

    def _loadfp (cls, filep, filename = '<memory>'):
        cache = None
        metadata = {}
        layers = {}
        config = None
        debug = False
        try:
            config = ConfigParser.ConfigParser()
            config.readfp(filep)

            if config.has_section("metadata"):
                for key in config.options("metadata"):
                    metadata[key] = config.get("metadata", key)

            if config.has_section("tilecache_options"):
                if 'path' in config.options("tilecache_options"):
                    for path in config.get("tilecache_options", "path").split(","):
                        sys.path.insert(0, path)
                if 'debug' in config.options("tilecache_options"):
                    debug = config.get("tilecache_options", "debug") not in ("false", "off", "no", "0")

            cache = cls.loadFromSection(config, "cache", Cache)

            layers = {}
            for section in config.sections():
                if section in cls.__slots__: continue
                try:
                    layers[section] = cls.loadFromSection(
                                            config, section, Layer,
                                            cache = cache)
                except Exception, E:
                    if debug:
                        print str(E)
                        print "".join(traceback.format_tb(sys.exc_info()[2]))

        except Exception, E:
            metadata['exception'] = E
            metadata['traceback'] = "".join(traceback.format_tb(sys.exc_info()[2]))
            if debug:
                print str(E)
                print "".join(traceback.format_tb(sys.exc_info()[2]))

        service = cls(cache, layers, metadata)
        service.files = (filename, )
        service.config = config
        return service

    loadfp = classmethod(_loadfp)

    def generate_crossdomain_xml(self):
        """Helper method for generating the XML content for a crossdomain.xml
           file, to be used to allow remote sites to access this content."""
        xml = ["""<?xml version="1.0"?>
<!DOCTYPE cross-domain-policy SYSTEM
  "http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd">
<cross-domain-policy>
        """]
        if self.metadata.has_key('crossdomain_sites'):
            sites = self.metadata['crossdomain_sites'].split(',')
            for site in sites:
                xml.append('  <allow-access-from domain="%s" />' % site)
        xml.append("</cross-domain-policy>")
        return ('text/xml', "\n".join(xml))

    def renderEmptyTile(self, ext = 'png'):
        try:
            import PIL.Image as Image
        except ImportError:
            raise Exception("Python Imaging Library required.")
        import StringIO

        image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        buffer = StringIO.StringIO()
        image.save(buffer, ext, optimize=1)
        buffer.seek(0)
        return buffer.read()

    def renderTile (self, tile, force = False):
        from warnings import warn
        start = time.time()

        # do more cache checking here: SRS, width, height, layers

        layer = tile.layer
        image = None
        if not force: image = self.cache.get(tile)
        if not image:
            if not force and layer.cache_only(tile.z):
#                raise Exception("Tile does not exist in fully defined cache.")
                if layer.debug:
                    sys.stderr.write(
                        "Cache (empty tile): %s, layer: %s, tile: x: %s, y: %s, z: %s, time: %s\n" % (
                            tile.bbox(), layer.name, tile.x, tile.y, tile.z, (time.time() - start)) )
                return (layer.mime_type, self.renderEmptyTile(layer.extension))

            data = layer.render(tile, force=force)
            if data:
                if not layer.metaTile:
                    image = self.cache.set(tile, data)
                else:
                    image = data
            else:
#                raise Exception("Zero length data returned from layer.")
                if layer.debug:
                    sys.stderr.write(
                        "Cache  (empty tile): %s, layer: %s, tile: x: %s, y: %s, z: %s, time: %s\n" % (
                             tile.bbox(), layer.name, tile.x, tile.y, tile.z, (time.time() - start)) )
                return (layer.mime_type, self.renderEmptyTile(layer.extension))

            if layer.debug:
                sys.stderr.write(
                    "Cache miss: %s, layer: %s, tile: x: %s, y: %s, z: %s, time: %s\n" % (
                        tile.bbox(), layer.name, tile.x, tile.y, tile.z, (time.time() - start)) )
        else:
            if layer.debug:
                sys.stderr.write(
                    "Cache hit: %s, layer: %s, tile: x: %s, y: %s, z: %s, time: %s\n" % (
                        tile.bbox(), layer.name, tile.x, tile.y, tile.z, (time.time() - start)) )

        return (layer.mime_type, image)

    def expireTile (self, tile):
        bbox  = tile.bounds()
        layer = tile.layer
        for z in range(len(layer.resolutions)):
            bottomleft = layer.getClosestCell(z, bbox[0:2])
            topright   = layer.getClosestCell(z, bbox[2:4])
            for y in range(bottomleft[1], topright[1] + 1):
                for x in range(bottomleft[0], topright[0] + 1):
                    coverage = Layer.Tile(layer,x,y,z)
                    self.cache.delete(coverage)

    def dispatchRequest (self, params, path_info="/", req_method="GET", host="http://example.com/"):
        if self.metadata.has_key('exception'):
            raise TileCacheException("%s\n%s" % (self.metadata['exception'], self.metadata['traceback']))
        if path_info.find("crossdomain.xml") != -1:
            return self.generate_crossdomain_xml()

        if path_info.split(".")[-1] == "kml":
            from CeraCache.Services.KML import KML
            return KML(self).parse(params, path_info, host)

        if params.has_key("scale") or params.has_key("SCALE"):
            from CeraCache.Services.WMTS import WMTS
            tile = WMTS(self).parse(params, path_info, host)
        elif params.has_key("service") or params.has_key("SERVICE") or \
             params.has_key("REQUEST") and params['REQUEST'] == "GetMap" or \
             params.has_key("request") and params['request'] == "GetMap":
            from CeraCache.Services.WMS import WMS
            tile = WMS(self).parse(params, path_info, host)     # standard WMS
        elif params.has_key("REQUEST") and params['REQUEST'] == "GetKml" or \
             params.has_key("request") and params['request'] == "GetKml":
            from CeraCache.Services.KMLWMS import KML
            return KML(self).parse(params, path_info, host)     # KML based on standard WMS
        elif params.has_key("L") or params.has_key("l") or \
             params.has_key("request") and params['request'] == "metadata":
            from CeraCache.Services.WorldWind import WorldWind
            tile = WorldWind(self).parse(params, path_info, host)
        elif params.has_key("interface"):
            from CeraCache.Services.TileService import TileService
            tile = TileService(self).parse(params, path_info, host)
        elif params.has_key("v") and \
             (params['v'] == "mgm" or params['v'] == "mgmaps"):
            from CeraCache.Services.MGMaps import MGMaps
            tile = MGMaps(self).parse(params, path_info, host)
        elif params.has_key("tile"):
            from CeraCache.Services.VETMS import VETMS
            tile = VETMS(self).parse(params, path_info, host)
        elif params.has_key("format") and params['format'].lower() == "json":
            from CeraCache.Services.JSON import JSON
            return JSON(self).parse(params, path_info, host)
        else:
            from CeraCache.Services.TMS import TMS
            tile = TMS(self).parse(params, path_info, host)

        try:
            import PIL.Image as Image
        except ImportError, E:
            raise Exception("Combining multiple layers requires Python Imaging Library.\n(Error was: %s)\n(Backtrace was: %s)" % (
                E, "".join(traceback.format_tb(sys.exc_info()[2]))
            ))

        try:
            import cStringIO as StringIO
        except ImportError:
            import StringIO

        if isinstance(tile, Layer.Tile):
            if req_method == 'DELETE':
                self.expireTile(tile)
                return ('text/plain', 'OK')
            else:
                (format, data) = self.renderTile(tile, params.has_key('FORCE'))

                if params.has_key('opacity'):
                    opacity = float(params['opacity'])
                else:
                    opacity = tile.layer.get_opacity(tile.z)

                if tile.layer.debug:
                    sys.stderr.write(
                        "Retrieved single layer tile: %s, layer: %s, tile: x: %s, y: %s, z: %s, opacity: %s\n" % (
                            tile.bbox(), tile.layer.name, tile.x, tile.y, tile.z, opacity) )

                if opacity == 1.0:
                    return (format, data)

                image = apply_opacity(tile, Image.open(StringIO.StringIO(data)), opacity)
                buffer = StringIO.StringIO()
                image.save(buffer, format.split('/')[1], optimize=1)
                buffer.seek(0)

                return (format, buffer.read())

        elif isinstance(tile, list):
            if req_method == 'DELETE':
                [self.expireTile(t) for t in tile]
                return ('text/plain', 'OK')
            else:
                result = None
                format = None
                data = None

                for t in tile:
                    try:
                        (format, data) = self.renderTile(t, params.has_key('FORCE'))
                        if t.layer.debug:
                            sys.stderr.write(
                                "Retrieved layered tile: %s, layer: %s, tile: x: %s, y: %s, z: %s\n" % (
                                     t.bbox(), t.layer.name, t.x, t.y, t.z) )
                    except Exception, e:
                        if t.layer.debug:
                            sys.stderr.write(
                                "Skipping tile: %s, layer: %s, tile: x: %s, y: %s, z: %s, e: %s\n" % (
                                    t.bbox(), t.layer.name, t.x, t.y, t.z, e)) 
#                                    "".join(traceback.format_tb(sys.exc_info()[2])) ) )
                        continue

                    image = Image.open(StringIO.StringIO(data))
                    opacity = t.layer.get_opacity(t.z)
                    if opacity != 1.0:
                        image = apply_opacity(t, image, opacity)

                    if not result:
                        result = image
                    else:
                        try:
                            # make sure the mask is not partially transparent
                            # as the source image already is

                            # old code:
                            result.paste(image, None, image.convert("RGBA"))

                            #image = image.convert("RGBA")
                            #r,g,b,a = image.split()
                            #a = a.point(lambda i: i != 0 and 255)
                            #result = Image.paste(result, image, mask=a)

                        except Exception, E:
                            raise Exception("Could not combine images: Is it possible that some layers are not \n8-bit transparent images? \n(Error was: %s)\n(Backtrace was: %s)" % (
                                E, "".join(traceback.format_tb(sys.exc_info()[2]))
                            ))

                buffer = StringIO.StringIO()
                result.save(buffer, format.split('/')[1], optimize=1)
                buffer.seek(0)

                return (format, buffer.read())
        else:
            return (tile.format, tile.data)

def modPythonHandler (apacheReq, service):
    from mod_python import apache, util
    try:
        if apacheReq.headers_in.has_key("X-Forwarded-Host"):
            host = "http://" + apacheReq.headers_in["X-Forwarded-Host"]
        else:
            host = "http://" + apacheReq.headers_in["Host"]
        host += apacheReq.uri[:-len(apacheReq.path_info)]
        format, image = service.dispatchRequest(
                                util.FieldStorage(apacheReq),
                                apacheReq.path_info,
                                apacheReq.method,
                                host )
        apacheReq.content_type = format
        apacheReq.status = apache.HTTP_OK
        if format.startswith("image/"):
            if service.cache.sendfile:
                apacheReq.headers_out['X-SendFile'] = image
            if service.cache.expire:
                apacheReq.headers_out['Expires'] = formatdate(time.time() + service.cache.expire, False, True)

        apacheReq.set_content_length(len(image))
        apacheReq.send_http_header()
        if format.startswith("image/") and service.cache.sendfile:
            apacheReq.write("")
        else:
            apacheReq.write(image)
    except TileCacheException, E:
        apacheReq.content_type = "text/plain"
        apacheReq.status = apache.HTTP_NOT_FOUND
        apacheReq.send_http_header()
        apacheReq.write("An error occurred: %s\n" % (str(E)))
    except Exception, E:
        apacheReq.content_type = "text/plain"
        apacheReq.status = apache.HTTP_INTERNAL_SERVER_ERROR
        apacheReq.send_http_header()
        apacheReq.write("An error occurred: %s\n%s\n" % (
            str(E),
            "".join(traceback.format_tb(sys.exc_info()[2]))))
    return apache.OK

def wsgiHandler (environ, start_response, service):
    from paste.request import parse_formvars
    try:
        path_info = host = ""


        if "PATH_INFO" in environ:
            path_info = environ["PATH_INFO"]

        if "HTTP_X_FORWARDED_HOST" in environ:
            host      = "http://" + environ["HTTP_X_FORWARDED_HOST"]
        elif "HTTP_HOST" in environ:
            host      = "http://" + environ["HTTP_HOST"]

        host += environ["SCRIPT_NAME"]
        req_method = environ["REQUEST_METHOD"]
        fields = parse_formvars(environ)

        format, image = service.dispatchRequest( fields, path_info, req_method, host )
        headers = [('Content-Type',format)]
        if format.startswith("image/"):
            if service.cache.sendfile:
                headers.append(('X-SendFile', image))
            if service.cache.expire:
                headers.append(('Expires', formatdate(time.time() + service.cache.expire, False, True)))

        start_response("200 OK", headers)
        if service.cache.sendfile and format.startswith("image/"):
            return []
        else:
            return [image]

    except TileCacheException, E:
        start_response("404 Tile Not Found", [('Content-Type','text/plain')])
        return ["An error occurred: %s" % (str(E))]
    except Exception, E:
        start_response("500 Internal Server Error", [('Content-Type','text/plain')])
        return ["An error occurred: %s\n%s\n" % (
            str(E),
            "".join(traceback.format_tb(sys.exc_info()[2])))]

def write_png(name, img):
    f = file(name, "w+")
    try:
        import msvcrt
        msvcrt.setmode(f.fileno(), os.O_BINARY)
    except:
        pass
    f.write(img)
    f.close()

def cgiHandler (service):
    try:
        params = {}
        input = cgi.FieldStorage()
        for key in input.keys(): params[key] = input[key].value
        path_info = host = ""

        if "PATH_INFO" in os.environ:
            path_info = os.environ["PATH_INFO"]

        if "HTTP_X_FORWARDED_HOST" in os.environ:
            host      = "http://" + os.environ["HTTP_X_FORWARDED_HOST"]
        elif "HTTP_HOST" in os.environ:
            host      = "http://" + os.environ["HTTP_HOST"]

        host += os.environ["SCRIPT_NAME"]
        req_method = os.environ["REQUEST_METHOD"]
        format, image = service.dispatchRequest( params, path_info, req_method, host )
        print "Content-type: %s" % format
        if format.startswith("image/"):
            if service.cache.sendfile:
                print "X-SendFile: %s" % image
            if service.cache.expire:
                print "Expires: %s" % formatdate(time.time() + service.cache.expire, False, True)
        print ""
        if (not service.cache.sendfile) or (not format.startswith("image/")):
            write_png('test.png', image)
            if sys.platform == "win32":
                binaryPrint(image)
            else:
                print image

    except TileCacheException, E:
        print "Cache-Control: max-age=10, must-revalidate" # make the client reload
        print "Content-type: text/plain\n"
        print "An error occurred: %s\n%s\n" % (str(E), "".join(traceback.format_tb(sys.exc_info()[2])))
    except Exception, E:
        print "Cache-Control: max-age=10, must-revalidate" # make the client reload
        print "Content-type: text/plain\n"
        print "An error occurred: %s\n%s\n" % (
            str(E),
            "".join(traceback.format_tb(sys.exc_info()[2])))

def genericHandler (service, params, path_info, host, req_method):
    try:
        format, image = service.dispatchRequest( params, path_info, req_method, host )
        return image, format

    except urllib2.HTTPError, E:
        return "An error occurred: %s\n%s\n%s\n" % (
            str(E), E.geturl(), ''.join(traceback.format_tb(sys.exc_info()[2]))), 'text/plain'
    except TileCacheException, E:
#        return "An error occurred: %s\n%s\n" % (
#            str(E), ''.join(traceback.format_tb(sys.exc_info()[2]))), 'text/plain'
        return service.renderEmptyTile(), 'image/png'
    except Exception, E:
        return "An error occurred: %s\n%s\n" % (
            str(E), ''.join(traceback.format_tb(sys.exc_info()[2]))), 'text/plain'

theService = {}
lastRead = {}
def handler (apacheReq):
    global theService, lastRead
    options = apacheReq.get_options()
    cfgs    = cfgfiles
    fileChanged = False
    if options.has_key("TileCacheConfig"):
        configFile = options["TileCacheConfig"]
        lastRead[configFile] = time.time()

        cfgs = cfgs + (configFile,)
        try:
            cfgTime = os.stat(configFile)[8]
            fileChanged = lastRead[configFile] < cfgTime
        except:
            pass
    else:
        configFile = 'default'

    if not theService.has_key(configFile) or fileChanged:
        theService[configFile] = Service.load(*cfgs)

    return modPythonHandler(apacheReq, theService[configFile])

def wsgiApp (environ, start_response):
    global theService
    cfgs    = cfgfiles
    if not theService:
        theService = Service.load(*cfgs)
    return wsgiHandler(environ, start_response, theService)

def binaryPrint(binary_data):
    """This function is designed to work around the fact that Python
       in Windows does not handle binary output correctly. This function
       will set the output to binary, and then write to stdout directly
       rather than using print."""
    try:
        import msvcrt
        msvcrt.setmode(sys.__stdout__.fileno(), os.O_BINARY)
    except:
        pass
    sys.stdout.write(binary_data)

def paste_deploy_app(global_conf, full_stack=True, **app_conf):
    if 'tilecache_config' in app_conf:
        cfgfiles = (app_conf['tilecache_config'],)
    else:
        raise TileCacheException("No tilecache_config key found in configuration. Please specify location of tilecache config file in your ini file.")
    theService = Service.load(*cfgfiles)
    if 'exception' in theService.metadata:
        raise theService.metadata['exception']

    def pdWsgiApp (environ,start_response):
        return wsgiHandler(environ,start_response,theService)

    return pdWsgiApp

if __name__ == '__main__':
    svc = Service.load(*cfgfiles)
    cgiHandler(svc)
