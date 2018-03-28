# BSD Licensed, Copyright (c) 2006-2008 MetaCarta, Inc.

import os, sys, math
from warnings import warn
from Client import WMS
from Service import TileCacheException

DEBUG = True

###############################################################################
# see: http://www.maptiler.org/google-maps-coordinates-tile-bounds-projection/
def LatLonToMeters(lat, lon):
    "Converts given lat/lon in WGS84 Datum to XY in Spherical Mercator EPSG:900913"

    originshift = 2 * math.pi * 6378137 / 2.0
    mx = lon * originshift / 180.0
    my = math.log( math.tan((90 + lat) * math.pi / 360.0 )) / (math.pi / 180.0)
    my = my * originshift / 180.0
    return mx, my

def PixelsToMeters(px, py, z, tileSize):
    "Converts pixel coordinates in given zoom level of pyramid to EPSG:900913"

    originshift = 2 * math.pi * 6378137 / 2.0
    res = originshift / (tileSize * 2**z)
    mx = px * res - originshift
    my = py * res - originshift
    return mx, my

def PixelsToTile(px, py, tileSize):
    "Returns a tile covering region in given pixel coordinates"

    tx = int( math.ceil( px / float(tileSize) ) - 1 )
    ty = int( math.ceil( py / float(tileSize) ) - 1 )
    return tx, ty

def MetersToPixels(mx, my, z, tileSize):
    "Converts EPSG:900913 to pyramid pixel coordinates in given zoom level"

    originshift = 2 * math.pi * 6378137 / 2.0
    res = originshift / (tileSize * 2**z)
    px = (mx + originshift) / res
    py = (my + originshift) / res
    return px, py

def MetersToTile(mx, my, z, tileSize):
    "Returns tile for given mercator coordinates"

    px, py = MetersToPixels(mx, my, z, tileSize)
    return PixelsToTile(px, py, tileSize)

def MetersToLatLon(mx, my):
    "Converts XY point from Spherical Mercator EPSG:900913 to lat/lon in WGS84 Datum"

    originshift = 2 * math.pi * 6378137 / 2.0
    lon = (mx / originshift) * 180.0
    lat = (my / originshift) * 180.0

    lat = 180 / math.pi * (2 * math.atan( math.exp( lat * math.pi / 180.0)) - math.pi / 2.0)
    return lat, lon

def TileBounds(tx, ty, z, tileSize, size = None):
    "Returns bounds of the given tile in EPSG:900913 coordinates"

    if not size:
        size = (1, 1)

    minx, miny = PixelsToMeters(tx*tileSize, ty*tileSize, z, tileSize)
    maxx, maxy = PixelsToMeters((tx+size[0])*tileSize, (ty+size[1])*tileSize, z, tileSize)
    return (minx, miny, maxx, maxy)

def TileLatLonBounds(tx, ty, z, tileSize, size = None):
    "Returns bounds of the given tile in latutude/longitude using WGS84 datum"

    bounds = TileBounds(tx, ty, z, tileSize, size)
    minLat, minLon = MetersToLatLon(bounds[0], bounds[1])
    maxLat, maxLon = MetersToLatLon(bounds[2], bounds[3])

    return (minLat, minLon, maxLat, maxLon)

def bbox_contains(bbox, (x, y), res):
    diff_x1 = abs(x - bbox[0])
    diff_x2 = abs(x - bbox[2])
    diff_y1 = abs(y - bbox[1])
    diff_y2 = abs(y - bbox[3])
    return (x >= bbox[0] or diff_x1 < res) and (x <= bbox[2] or diff_x2 < res) \
       and (y >= bbox[1] or diff_y1 < res) and (y <= bbox[3] or diff_y2 < res)

def lines_intersect(x1, (y10, y11), (x20, x21), y2):
    return x20 <= x1 and x21 >= x1 and y10 <= y2 and y11 >= y2

def boxes_intersect(self_bbox, bbox):
    if (lines_intersect(self_bbox[0], (self_bbox[1], self_bbox[2]), (bbox[0], bbox[2]), bbox[1]) or
        lines_intersect(self_bbox[0], (self_bbox[1], self_bbox[2]), (bbox[0], bbox[2]), bbox[3]) or
        lines_intersect(self_bbox[2], (self_bbox[1], self_bbox[2]), (bbox[0], bbox[2]), bbox[1]) or
        lines_intersect(self_bbox[2], (self_bbox[1], self_bbox[2]), (bbox[0], bbox[2]), bbox[3]) or
        lines_intersect(bbox[0], (bbox[1], bbox[2]), (self_bbox[0], self_bbox[2]), self_bbox[1]) or
        lines_intersect(bbox[0], (bbox[1], bbox[2]), (self_bbox[0], self_bbox[2]), self_bbox[3]) or
        lines_intersect(bbox[2], (bbox[1], bbox[2]), (self_bbox[0], self_bbox[2]), self_bbox[1]) or
        lines_intersect(bbox[2], (bbox[1], bbox[2]), (self_bbox[0], self_bbox[2]), self_bbox[3])):
            return True
    return False

###############################################################################
class Tile (object):
    """
    >>> l = Layer("name", maxresolution=0.019914, size="256,256")
    >>> t = Tile(l, 18, 20, 0)
    """
    __slots__ = ( "layer", "x", "y", "z", "data" )
    def __init__ (self, layer, x, y, z):
        """
        >>> l = Layer("name", maxresolution=0.019914, size="256,256")
        >>> t = Tile(l, 18, 20, 0)
        >>> t.x
        18
        >>> t.y
        20
        >>> t.z
        0
        >>> print t.data
        None
        """
        self.layer = layer
        self.x = x
        self.y = y
        self.z = z
        self.data = None

    def size (self):
        """
        >>> l = Layer("name", maxresolution=0.019914, size="256,256")
        >>> t = Tile(l, 18, 20, 0)
        >>> t.size()
        [256, 256]
        """
        return self.layer.size

    def bounds (self):
        """
        >>> l = Layer("name", maxresolution=0.019914)
        >>> t = Tile(l, 18, 20, 0)
        >>> t.bounds()
        (-88.236288000000002, 11.959680000000006, -83.138303999999991, 17.057664000000003)
        """
        if (self.layer.tms_type == "google"):
            miny, minx, maxy, maxx = TileLatLonBounds(self.x, self.y, self.z, self.layer.size[0])
            return (minx, miny, maxx, maxy)

        res  = self.layer.resolutions[self.z]
        minx = self.layer.bbox[0] + (res * self.x * self.layer.size[0])       # self.layer.realbbox[0]
        maxx = self.layer.bbox[0] + (res * (self.x + 1) * self.layer.size[0]) # self.layer.realbbox[2]
        miny = self.layer.bbox[1] + (res * self.y * self.layer.size[1])       # self.layer.realbbox[1]
        maxy = self.layer.bbox[1] + (res * (self.y + 1) * self.layer.size[1])  # self.layer.realbbox[3]
        return (minx, miny, maxx, maxy)

    def bbox (self):
        """
        >>> l = Layer("name", maxresolution=0.019914)
        >>> t = Tile(l, 18, 20, 0)
        >>> t.bbox()
        '-88.236288,11.95968,-83.138304,17.057664'
        """
        return ",".join(map(str, self.bounds()))

class MetaTile (Tile):

    __slots__ = ( "exact" )
    def __init__ (self, layer, x, y, z, exact):
        super(MetaTile, self).__init__(layer, x, y, z)
        self.exact = exact

    def actualSize (self):
        """
        >>> l = MetaLayer("name")
        >>> t = MetaTile(l, 0,0,0)
        >>> t.actualSize()
        (256, 256)
        """
        metaCols, metaRows = self.layer.getMetaSize(self.z)
        return ( self.layer.size[0] * metaCols,
                 self.layer.size[1] * metaRows )

    def size (self):
        actual = self.actualSize()
        return ( actual[0] + self.layer.metaBuffer[0] * 2,
                 actual[1] + self.layer.metaBuffer[1] * 2 )

    def bounds (self):
        tilesize   = self.actualSize()
        res        = self.layer.resolutions[self.z]
        buffer     = (res * self.layer.metaBuffer[0], res * self.layer.metaBuffer[1])

        if (self.layer.tms_type == "google"):
            if self.exact:
                miny, minx, maxy, maxx = TileLatLonBounds(
                    self.x, self.y, self.z,
                    self.layer.size[1], self.layer.metaSize)
            else:
                miny, minx, maxy, maxx = TileLatLonBounds(
                    self.x * self.layer.metaSize[0],
                    self.y * self.layer.metaSize[1],
                    self.z, self.layer.size[1], self.layer.metaSize)

#            maxx = minx + (maxx - minx) * tilesize[0] / self.layer.size[0]
#            maxy = miny + (maxy - miny) * tilesize[1] / self.layer.size[1]

#            miny = -90. + self.y * metaHeight # + res * tilesize[1] + res * self.layer.size[1] - buffer[1]  #self.layer.bbox[1] + self.y * metaHeight - buffer[1]
#            maxy = miny + res * tilesize[1] + 2 * buffer[1]
        else:
            metaWidth  = res * self.layer.metaSize[0] * self.layer.size[0] # tilesize[0]
            metaHeight = res * self.layer.metaSize[1] * self.layer.size[1] # tilesize[1]
            minx = -180. + self.x * metaWidth  #self.layer.bbox[0] + self.x * metaWidth  - buffer[0]
            maxx = minx + res * tilesize[0]
            miny = -90. + self.y * metaHeight  #self.layer.bbox[1] + self.y * metaHeight - buffer[1]
            maxy = miny + res * tilesize[1]

        minx = minx - buffer[0]
        miny = miny - buffer[1]
        maxx = maxx + buffer[0]
        maxy = maxy + buffer[1]
        return (minx, miny, maxx, maxy)

###############################################################################
class Layer (object):
    __slots__ = ( "name", "layers", "paletted", "bbox", "data_extent",
                  "size", "resolutions", "extension", "srs",
                  "cache", "debug", "description",
                  "watermarkimage", "watermarkopacity",
                  "extent_type", "tms_type", "units", "mime_type",
                  "spherical_mercator", "metadata", "realbbox", "aspect",
                  "cache_prefix", "cache_only", "levels", "opacity")

    config_properties = [
        {'name':'spherical_mercator', 'description':'Layer is in spherical mercator. (Overrides bbox, maxresolution, SRS, Units)', 'type': 'boolean'},
        {'name':'layers', 'description': 'Comma seperated list of layers associated with this layer.'},
        {'name':'extension', 'description':'File type extension', 'default':'png'},
        {'name':'bbox', 'description':'Bounding box of the layer grid', 'default':'-180,-90,180,90'},
        {'name':'srs', 'description':'Spatial Reference System for the layer', 'default':'EPSG:4326'},
        {'name':'data_extent', 'description':'Bounding box of the layer data. (Same SRS as the layer grid.)', 'default':"", 'type': 'map'},
        {'name':'cache_prefix', 'description':'Prefix to be prepended to tile name in cache', 'default':"", 'type': 'string'},
        {'name':'cache_only', 'description':'layer is fully defined by cache content', 'default': False, 'type': 'boolean'},
        {'name':'levels', 'description': 'max number of levels supported by this layer', 'default': 13, 'type': 'int'},
        {'name':'opacity', 'description': 'make this layer transparent using the given value', 'default': "1.0", 'type': 'string'}
    ]

    def __init__ (self, name, layers = None, bbox = (-180, -90, 180, 90),
                        data_extent = None,
                        srs  = "EPSG:4326", description = "", maxresolution = None,
                        size = (256, 256), levels = 13, resolutions = None,
                        extension = "png", mime_type = None, cache = None,  debug = False,
                        watermarkimage = None, watermarkopacity = 0.2,
                        spherical_mercator = False,
                        extent_type = "strict", units = "degrees", tms_type = "",
                        cache_prefix = "", cache_only = False, 
                        opacity = "1.0", **kwargs ):
        """Take in parameters, usually from a config file, and create a Layer.

        >>> l = Layer("Name", bbox="-12,17,22,36", debug="no")
        >>> l.bbox
        [-12.0, 17.0, 22.0, 36.0]
        >>> l.debug
        False

        >>> l = Layer("name", spherical_mercator="yes")
        >>> round(l.resolutions[0])
        156543.0
        """

        self.name   = name
        self.description = description
        self.layers = layers or name
        self.paletted = False
        self.cache_prefix = cache_prefix
        if isinstance(levels, str):
            self.levels = int(levels)
        else:
            self.levels = levels

        if isinstance(cache_only, str):
            if cache_only.lower() in ("false", "off", "no", "0"):
                cache_only_func = lambda z: False
            elif cache_only.lower() in ("true", "on", "yes", "1"):
                cache_only_func = lambda z: True
            else:
                r = map(int, cache_only.split('-'))
                if len(r) < 2:
                    cache_only_func = lambda z: z == r[0]
                else:
                    cache_only_func = lambda z: z >= r[0] and z <= r[1]
        else:
            cache_only_func = lambda z : False

        self.cache_only = cache_only_func

        if isinstance(spherical_mercator, str):
            spherical_mercator = spherical_mercator.lower() not in ("false", "off", "no", "0")
        self.spherical_mercator = spherical_mercator
        if self.spherical_mercator:
            bbox = "-20037508.34,-20037508.34,20037508.34,20037508.34"
            maxresolution = "156543.0339"
            if srs == "EPSG:4326":
                srs = "EPSG:900913"
            units = "meters"

        if isinstance(bbox, str):
            bbox = map(float, bbox.split(","))
        self.bbox = bbox

        if isinstance(data_extent, str):
            data_extent = map(float, data_extent.split(","))
        self.data_extent = data_extent or bbox

        if isinstance(size, str):
            size = map(int, size.split(","))
        self.size = size

        self.units = units

        self.srs  = srs

        if extension.lower() == 'jpg':
            extension = 'jpeg' # MIME
        elif extension.lower() == 'png256':
            extension = 'png'
            self.paletted = True
        self.extension = extension.lower()
        self.mime_type = mime_type or self.format()

        if isinstance(debug, str):
            debug = debug.lower() not in ("false", "off", "no", "0")
        self.debug = debug

        self.cache = cache
        self.extent_type = extent_type
        self.tms_type = tms_type
        self.aspect = 1
        self.transparent = True
        self.opacity = eval(opacity)

        if resolutions:
            if isinstance(resolutions, str):
                resolutions = map(float,resolutions.split(","))
            self.resolutions = resolutions
        else:
            maxRes = None
            if not maxresolution:
                width  = 360.0    # bbox[2] - bbox[0]
                height = 180.0    # bbox[3] - bbox[1]
                if width >= height:
                    self.aspect = int( float(width) / height + .5 ) # round up
                    maxRes = float(width) / (size[0] * self.aspect)
                else:
                    self.aspect = int( width / float(height)  + .5 ) # round up
                    maxRes = (float(height) / size[1]) / self.aspect
            else:
                maxRes = float(maxresolution)
            self.resolutions = [maxRes / 2 ** i for i in range(int(levels))]

        self.watermarkimage = watermarkimage

        self.watermarkopacity = float(watermarkopacity)

        self.metadata = {}

        prefix_len = len("metadata_")
        for key in kwargs:
            if key.startswith("metadata_"):
                self.metadata[key[prefix_len:]] = kwargs[key]

    def get_opacity(self, zoom):
        if type(self.opacity) == type({}):
            if self.opacity.has_key(zoom):
                return float(self.opacity[zoom])
            if self.opacity.has_key("default"):
                return float(self.opacity["default"])
            return 1.0
        return float(self.opacity)
            
    def isMetaTileLayer(self):
        return False

    def getResolution (self, (minx, miny, maxx, maxy), size = None):
        """
        >>> l = Layer("name")
        >>> l.getResolution((-180, -90, 180, 90))
        0.703125
        """
        if size is None:
            size = self.size
        return max( float(maxx - minx) / size[0],
                    float(maxy - miny) / size[1] )

    def getClosestLevel (self, res, size = [256, 256]):
        diff = sys.maxint
        z = None
        for i in range(len(self.resolutions)):
            if diff > abs( self.resolutions[i] - res ):
                diff = abs( self.resolutions[i] - res )
                z = i
        return z

    def getLevel (self, res, size = [256, 256]):
        """
        >>> l = Layer("name")
        >>> l.getLevel(.703125)
        0
        """

        max_diff = res / max(size[0], size[1])
        z = None
        for i in range(len(self.resolutions)):
            if abs( self.resolutions[i] - res ) < max_diff:
                res = self.resolutions[i]
                z = i
                break
        if z is None:
            raise TileCacheException("can't find resolution index for %f. Available resolutions are: \n%s" % (res, self.resolutions))
        return z

    def getExactResolution(self, (minx, miny, maxx, maxy), exact = True):
        res = self.getResolution((minx, miny, maxx, maxy))
        if exact:
            z = self.getLevel(res, self.size)
        else:
            z = self.getClosestLevel(res, self.size)
        return (self.resolutions[z], z)

    def getCell (self, (minx, miny, maxx, maxy), exact = True, check_overlap = None): #, tile = None):
        """
        Returns x, y, z

        >>> l = Layer("name")
        >>> l.bbox
        (-180, -90, 180, 90)
        >>> l.resolutions[0]
        0.703125
        >>> l.getCell((-180., -90., 180., 90.))
        (0, 0, 0)
        >>> l.getCell((-45.,-45.,0.,0.))
        (3, 1, 2)
        """

        if check_overlap is None:
            check_overlap = exact

        x = y = None
        res, z = self.getExactResolution((minx, miny, maxx, maxy), exact)

        if check_overlap and self.extent_type == "strict" and not self.contains((minx, miny), res):
            raise TileCacheException("Lower left corner (%f, %f) is outside layer bounds %s. \nTo remove this condition, set extent_type=loose in your configuration."
                     % (minx, miny, self.bbox))
            return None

#        x0 = (minx - self.bbox[0]) / (res * self.size[0])
#        y0 = (miny - self.bbox[1]) / (res * self.size[1] / self.aspect)

#        if (tile is not None):
#            x = int(tile[0])
#            y = int(tile[1])
#            if (self.tms_type == "google"):
#                maxY = int(
#                  round( (self.bbox[3] - self.bbox[1]) / (res * self.size[1] / self.aspect) )
#                ) - 1
#                y = int(maxY - y)
#        else:
#        x = int(x0)
#        y = int(y0)
#        if (self.tms_type == "google"):
#            maxY = int(
#              round( (self.bbox[3] - self.bbox[1]) / (res * self.size[1] / self.aspect) )
#            ) - 1
#            y = maxY - int((1.5*maxY - y0)/2.0) + 1

#        tilex = ((x * res * self.size[0]) + self.bbox[0])
#        tiley = (((y * res * self.size[1] / self.aspect) + self.bbox[1])) * self.aspect

        if (self.tms_type == "google"):
            if (exact):
                xm, ym = LatLonToMeters((miny + maxy)/2.0, (minx + maxx)/2.0)
            else:
                xm, ym = LatLonToMeters(miny, minx)
            x, y = MetersToTile(xm, ym, z, self.size[0])
            tiley, tilex, yd, xd = TileLatLonBounds(x, y, z, self.size[0])
        else:
            x0 = (minx - self.bbox[0]) / (res * self.size[0])
            y0 = (miny - self.bbox[1]) / (res * self.size[1] / self.aspect)
            x = int(x0)
            y = int(y0)
            tilex = ((x * res * self.size[0]) + self.bbox[0])
            tiley = (((y * res * self.size[1] / self.aspect) + self.bbox[1])) * self.aspect

        if exact:
            if (abs(minx - tilex)  / res > 1):
                raise TileCacheException("Current x value %f is too far from tile corner x %f" % (minx, tilex))
            if (abs(miny - tiley) / res > 1):
                raise TileCacheException("Current y value %f is too far from tile corner y %f" % (miny, tiley))

        self.realbbox = (minx, miny, maxx, maxy)
        return (x, y, z)

    def getClosestCell (self, z, (minx, miny)):
        """
        >>> l = Layer("name")
        >>> l.getClosestCell(2, (84, 17))
        (6, 2, 2)
        """
        res = self.resolutions[z]
        maxx = minx + self.size[0] * res
        maxy = miny + self.size[1] * res
        return self.getCell((minx, miny, maxx, maxy), False)

    def getTile (self, bbox): #, tile = None):
        """
        >>> l = Layer("name")
        >>> l.getTile((-180, -90, 180, 90)).bbox()
        '-180.0,-90.0,180.0,90.0'
        """

        res, z = self.getExactResolution(bbox, True)
        if (boxes_intersect(self.bbox, bbox) or
            bbox_contains(self.bbox, (bbox[0], bbox[1]), res) or
            bbox_contains(self.bbox, (bbox[2], bbox[1]), res) or
            bbox_contains(self.bbox, (bbox[0], bbox[3]), res) or
            bbox_contains(self.bbox, (bbox[2], bbox[3]), res) or
            bbox_contains(bbox, (self.bbox[0], self.bbox[1]), res) or
            bbox_contains(bbox, (self.bbox[2], self.bbox[1]), res) or
            bbox_contains(bbox, (self.bbox[0], self.bbox[3]), res) or
            bbox_contains(bbox, (self.bbox[2], self.bbox[3]), res)):
        # boxes do overlap
            coord = self.getCell(bbox, True, False) # , tile)
            if not coord:
                return None
            return Tile(self, *coord)

        return None

    def contains (self, pt, res = 0):
        """
        >>> l = Layer("name")
        >>> l.contains((0,0))
        True
        >>> l.contains((185, 94))
        False
        """
        return bbox_contains(self.bbox, pt, res)

    def grid (self, z):
        """
        Returns size of grid at a particular zoom level

        >>> l = Layer("name")
        >>> l.grid(3)
        (16.0, 8.0)
        """
        width  = (self.bbox[2] - self.bbox[0]) / (self.resolutions[z] * self.size[0])
        height = (self.bbox[3] - self.bbox[1]) / (self.resolutions[z] * self.size[1])
        return (width, height)

    def format (self):
        """
        >>> l = Layer("name")
        >>> l.format()
        'image/png'
        """
        return "image/" + self.extension

    def renderTile (self, tile):
        # To be implemented by subclasses
        pass

    def render (self, tile):
        return self.renderTile(tile)

class MetaLayer (Layer):
    __slots__ = ('metaTile', 'metaSize', 'metaBuffer', 'metaTileExact')

    config_properties = Layer.config_properties + [
      {'name':'name', 'description': 'Name of Layer'},
      {'name':'metaTile', 'description': 'Should metatiling be used on this layer?', 'default': 'false', 'type':'boolean'},
      {'name': 'metaSize', 'description': 'Comma seperated-pair of numbers, defininig the tiles included in a single size', 'default': "1,1"},
      {'name': 'metaBuffer', 'description': 'Number of pixels outside the metatile to include in the render request.'},
      {'name':'metaTileExact', 'description': 'Metatiling on this layer will place metatiles exactly?', 'default': 'false', 'type':'boolean'},
    ]

    def __init__ (self, name, metatile = "", metasize = (5, 5),
                              metabuffer = (0, 0), **kwargs):
        Layer.__init__(self, name, **kwargs)
        self.metaTile = metatile.lower() not in ("false", "no", "off", "0")
        self.metaTileExact = metatile.lower() not in ("false", "no", "off", "0")
        if isinstance(metasize, str):
            metasize = map(int,metasize.split(","))
        if isinstance(metabuffer, str):
            metabuffer = map(int, metabuffer.split(","))
            if len(metabuffer) == 1:
                metabuffer = (metabuffer[0], metabuffer[0])
        self.metaSize    = metasize
        self.metaBuffer  = metabuffer

    def isMetaTileLayer(self):
        return self.metaTile

    def isMetaTileExactLayer(self):
        return self.metaTileExact

    # always use maximum extend for metalayers
    def grid (self, z):
        width  = 360.0 / (self.resolutions[z] * self.size[0])
        height = 180.0 / (self.resolutions[z] * self.size[1])
        return (width, height)

    def getMetaSize (self, z):
        if not self.metaTile: return (1,1)
        maxcol, maxrow = self.grid(z)
        return ( min(self.metaSize[0], int(maxcol + 1)),
                 min(self.metaSize[1], int(maxrow + 1)) )

    def getMetaTile (self, tile):
        if self.metaTileExact:
            x = tile.x
            y = tile.y
        else:
            x = int(tile.x / self.metaSize[0])
            y = int(tile.y / self.metaSize[1])
        return MetaTile(self, x, y, tile.z, self.metaTileExact)

    def renderMetaTile (self, metatile, tile):

        data = self.renderTile(metatile)

        metaCols, metaRows = self.getMetaSize(metatile.z)
        metaHeight = metaRows * self.size[1] + 2 * self.metaBuffer[1]
        if self.debug:
            print >> sys.stderr, "metaCols, metaRows: %d, %d" % (metaCols, metaRows)
            print >> sys.stderr, "metaHeight: %d" % metaHeight

        try:
            import PIL.Image as Image
        except ImportError:
            raise Exception("Meta-tiling requires Python Imaging Library.")
        try:
            import cStringIO as StringIO
        except ImportError:
            import StringIO

        image = Image.open( StringIO.StringIO(data) )
        buffer = StringIO.StringIO()
        if image.info.has_key('transparency'):
            image.save(buffer, self.extension, transparency=image.info['transparency'], optimize=1)
        else:
            image.save(buffer, self.extension, optimize=1)

#        buffer.seek(0)
#        subdata = buffer.read()
#        output = file("abc.png", "wb")
#        output.write(subdata)
#        output.close()

        for i in range(metaCols):
            for j in range(metaRows):
                minx = i * self.size[0] + self.metaBuffer[0]
                maxx = minx + self.size[0]
                ### this next calculation is because image origin is (top,left)
                maxy = metaHeight - (j * self.size[1] + self.metaBuffer[1])
                miny = maxy - self.size[1]
                if self.debug:
                    print >> sys.stderr, "cropped image", (minx, miny, maxx, maxy)

                subimage = image.crop((minx, miny, maxx, maxy))
                buffer = StringIO.StringIO()
                if image.info.has_key('transparency'):
                    subimage.save(buffer, self.extension, transparency=image.info['transparency'], optimize=1)
                else:
                    subimage.save(buffer, self.extension, optimize=1)
                buffer.seek(0)
                subdata = buffer.read()
                if metatile.exact:
                    x = metatile.x + i
                    y = metatile.y + j
                else:
                    x = metatile.x * self.metaSize[0] + i
                    y = metatile.y * self.metaSize[1] + j
                if self.debug:
                    print >> sys.stderr, "Creating subtile %d, %d, %d" % (x, y, tile.z)
                subtile = Tile( self, x, y, metatile.z )
                if self.watermarkimage:
                    subdata = self.watermark(subdata)
                self.cache.set( subtile, subdata )
                if True: #x == tile.x and y == tile.y:
                    tile.data = subdata

        return tile.data

    def render (self, tile, force=False):
        if self.metaTile:
            metatile = self.getMetaTile(tile)
            needs_locking = self.metaSize[0] > 1 or self.metaSize[1] > 1
            try:
                if needs_locking:
                    self.cache.lock(metatile)
                image = None
                if not force:
                    image = self.cache.get(tile)
                if not image:
                    image = self.renderMetaTile(metatile, tile)
            finally:
                if needs_locking:
                    self.cache.unlock(metatile)
            return image
        else:
            if self.watermarkimage:
                return self.watermark(self.renderTile(tile))
            else:
                return self.renderTile(tile)

    def watermark (self, img):
        import StringIO, Image, ImageEnhance
        tileImage = Image.open( StringIO.StringIO(img) )
        wmark = Image.open(self.watermarkimage)
        assert self.watermarkopacity >= 0 and self.watermarkopacity <= 1
        if wmark.mode != 'RGBA':
            wmark = wmark.convert('RGBA')
        else:
            wmark = wmark.copy()
        alpha = wmark.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(self.watermarkopacity)
        wmark.putalpha(alpha)
        if tileImage.mode != 'RGBA':
            tileImage = tileImage.convert('RGBA')
        watermarkedImage = Image.new('RGBA', tileImage.size, (0,0,0,0))
        watermarkedImage.paste(wmark, (0,0))
        watermarkedImage = Image.composite(watermarkedImage, tileImage, watermarkedImage)
        buffer = StringIO.StringIO()
        if watermarkedImage.info.has_key('transparency'):
            watermarkedImage.save(buffer, self.extension, transparency=compositeImage.info['transparency'])
        else:
            watermarkedImage.save(buffer, self.extension)
        buffer.seek(0)
        return buffer.read()

if __name__ == "__main__":
    import doctest
    doctest.testmod()
