# BSD Licensed, Copyright (c) 2006-2008 MetaCarta, Inc.

from CeraCache.Layer import MetaLayer
import CeraCache.Client as WMSClient

 
def distance2(a, b): 
    return (a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1]) + (a[2] - b[2]) * (a[2] - b[2]) 
 
def makeColorTransparent(image, color, thresh2 = 0): 
    try:
        import PIL.Image as Image
        import PIL.ImageMath as ImageMath 
    except ImportError:
        raise Exception("Image manipulation Python Imaging Library.")

    image = image.convert("RGBA") 
    red, green, blue, alpha = image.split() 
    image.putalpha(ImageMath.eval("convert((((((t - d(c, (r, g, b))) >> 31) + 1) ^ 1) * a), 'L')", 
        t=thresh2, d=distance2, c=color, r=red, g=green, b=blue, a=alpha))
    return image 
 
class WMS(MetaLayer):
    config_properties = [
      {'name':'name', 'description': 'Name of Layer'},
      {'name':'url', 'description': 'URL of Remote Layer'},
      {'name':'user', 'description': 'Username of remote server: used for basic-auth protected backend WMS layers.'},
      {'name':'password', 'description': 'Password of remote server: Use for basic-auth protected backend WMS layers.'},
      {'name':'local_script', 'description': 'WMS CGI script to execute instead of remote WMS command.'},
      {'name':'bgcolor', 'description': 'background color.', 'default': '0,0,0'},
      {'name':'make_transparent', 'description': 'make background color transparent.', 'default': '0'},
    ] + MetaLayer.config_properties

    def __init__ (self, name, url = None, user = None, password = None, 
            local_script = None, bgcolor = '255,255,255', make_transparent = '0', **kwargs):
        MetaLayer.__init__(self, name, **kwargs)
        self.url = url
        self.user = user
        self.password = password
        self.local_script = local_script
        self.bgcolor = map(int, bgcolor.split(','))
        self.make_transparent = make_transparent not in ("false", "off", "no", "0")

    def transform_bbox(self, bbox):
        import osgeo.ogr

        # figure out whether we need to transform
        code = int(self.srs.split(':')[1])
        if code == 4326:
            return bbox

        # create coordinate transformation
        src = osgeo.ogr.osr.SpatialReference()
        dest = osgeo.ogr.osr.SpatialReference()
        src.ImportFromEPSG(4326)
        dest.ImportFromEPSG(code)

        transform = osgeo.ogr.osr.CoordinateTransformation(src, dest)

        # collect coordinates
        bbox = map(float, bbox.split(','))
        pt1 = transform.TransformPoint(float(bbox[0]), float(bbox[1]))
        pt2 = transform.TransformPoint(float(bbox[2]), float(bbox[3]))
        return "%f,%f,%f,%f" % (pt1[0], pt1[1], pt2[0], pt2[1])

    def renderTile(self, tile):
        if self.local_script is None:
            wms = WMSClient.WMS( self.url, {
              "bbox": self.transform_bbox(tile.bbox()),
              "width": tile.size()[0],
              "height": tile.size()[1],
              "srs": self.srs,
              "format": self.mime_type,
              "layers": self.layers,
              "transparent": self.transparent
            }, self.user, self.password)
            tile.data, response = wms.fetch()

            if self.make_transparent:
                try:
                    import PIL.Image as Image
                except ImportError:
                    raise Exception("Image manipulation Python Imaging Library.")
                try:
                    import cStringIO as StringIO
                except ImportError:
                    import StringIO

                image = makeColorTransparent(Image.open(StringIO.StringIO(tile.data)), self.bgcolor)

                buffer = StringIO.StringIO()
                image.save(buffer, self.extension, optimize=1)

                buffer.seek(0)
                tile.data = buffer.read()

            return tile.data

        # execute local script instead
        wms = WMSClient.LocalWMS( self.url, {
          "bbox": tile.bbox(),
          "width": tile.size()[0],
          "height": tile.size()[1],
          "srs": self.srs,
          "format": self.mime_type,
          "layers": self.layers,
        }, self.local_script)
        tile.data = wms.fetch()
        return tile.data
