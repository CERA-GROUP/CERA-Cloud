# BSD Licensed, Copyright (c) 2006-2008 MetaCarta, Inc.

from CeraCache.Layer import MetaLayer
from CeraCache.Service import TileCacheException

import osgeo.gdal as gdal
import osgeo.gdal_array as gdalarray
import numpy
import PIL
import os

def save_file(name, im):
    import StringIO

    buffer = StringIO.StringIO()
    im.save(buffer, 'png')

    buffer.seek(0)
    subdata = buffer.read()
    output = file(name, "wb")
    output.write(subdata)
    output.close()

class GDAL(MetaLayer):
    """
    The GDAL Layer allows you to set up any GDAL datasource in TileCache.

    Areas not covered by the image will be transparent in formats which
    support transparency. The GDAL transparency is maintained. All bands
    of an image are read from the source file at this time.

    This Layer does not support images where north is not up.

    Special effort is taken when the GeoTransform on the image is the default 
    (0.0, 1.0, 0.0, 0.0, 0.0, 1.0): In that case, the geotransform is 
    replaced with (0.0, 1.0, 0.0, self.ds.RasterYSize, 0.0, -1.0) . This allows
    one to use the GDAL layer with non-georeferenced images: Simply specify a 
    bbox=0,0,size_x,size_y, and then you can use the image in TileCache. This is
    likely a better idea than using the Image layer, if you can install GDAL,
    since GDAL may be more efficient in managing subsetting of files, especially
    geographic sized ones, due to its ability to support overviews on files it is
    reading.

    This layer depends on:
     * GDAL 1.5 with Python Bindings
     * PIL
     * numpy
    """

    config_properties = [
      {'name':'name', 'description': 'Name of Layer'}, 
      {'name':'file', 'description': 'GDAL-readable file path.'},
      {'name':'bgcolor', 'description': 'background color.', 'default': '0,0,255,0'},
    ] + MetaLayer.config_properties 

    def __init__ (self, name, file = None, bgcolor = '0,0,255,0', **kwargs):

        # avoid scanning the directory before opening the file
        # see here for an explanation: https://trac.osgeo.org/gdal/ticket/2158
        gdal.SetConfigOption('GDAL_DISABLE_READDIR_ON_OPEN', 'TRUE')

        gdal.UseExceptions()
        MetaLayer.__init__(self, name, **kwargs) 

        self.file = file
        self.bgcolor = bgcolor
        self.ds = None

    def renderTile(self, tile):
        if self.ds is None:
            if self.file and os.path.exists(self.file):
                self.ds = gdal.Open(self.file)
                self.geo_transform = self.ds.GetGeoTransform()
                if self.geo_transform[2] != 0 or self.geo_transform[4] != 0:
                    raise Exception("Image is not 'north-up', can not use.")
                if self.geo_transform == (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
                    self.geo_transform = (0.0, 1.0, 0.0, self.ds.RasterYSize, 0.0, -1.0)
                size = [self.ds.RasterXSize, self.ds.RasterYSize]
                xform = self.geo_transform
                self.data_extent = [
                   xform[0] + self.ds.RasterYSize * xform[2],
                   xform[3] + self.ds.RasterYSize * xform[5],  
                   xform[0] + self.ds.RasterXSize * xform[1],
                   xform[3] + self.ds.RasterXSize * xform[4]
                ]

                self.bgcolor = map(int, self.bgcolor.split(','))
                if len(self.bgcolor) == 4:
                    self.bgcolor = (self.bgcolor[0], self.bgcolor[1], self.bgcolor[2], self.bgcolor[3])
                elif len(bgcolor) == 3:
                    self.bgcolor = (self.bgcolor[0], self.bgcolor[1], self.bgcolor[2], 255)
                else:
                    raise TileCacheException("Bogus format for bgcolor.")

            else:
                raise TileCacheException("GDAL datasource does not exist: %s." % self.file)

        import PIL.Image as PILImage 
        import StringIO
        bounds = tile.bounds()
        im = None
        mask = None

        # If the image is entirely outside the bounds, don't bother doing anything with it:
        # just return an 'empty' tile.

        if not (bounds[2] < self.data_extent[0] or bounds[0] > self.data_extent[2] or
            bounds[3] < self.data_extent[1] or bounds[1] > self.data_extent[3]):
            tile_offset_left = tile_offset_top = 0

            target_size = tile.size()

            off_x = int((bounds[0] - self.geo_transform[0]) / self.geo_transform[1]);
            off_y = int((bounds[3] - self.geo_transform[3]) / self.geo_transform[5]);
            width_x = int(((bounds[2] - self.geo_transform[0]) / self.geo_transform[1]) - off_x);
            width_y = int(((bounds[1] - self.geo_transform[3]) / self.geo_transform[5]) - off_y);

            # Prevent from reading off the sides of an image
            if off_x + width_x > self.ds.RasterXSize:
                oversize_right = off_x + width_x - self.ds.RasterXSize
                target_size = [
                   target_size[0] - int(float(oversize_right) / width_x * target_size[0]),
                   target_size[1]
                   ]
                width_x = self.ds.RasterXSize - off_x

            if off_x < 0:
                oversize_left = -off_x
                tile_offset_left = int(float(oversize_left) / width_x * target_size[0])
                target_size = [
                   target_size[0] - int(float(oversize_left) / width_x * target_size[0]), 
                   target_size[1],
                   ]
                width_x = width_x + off_x
                off_x = 0

            if off_y + width_y > self.ds.RasterYSize:
                oversize_bottom = off_y + width_y - self.ds.RasterYSize
                target_size = [
                   target_size[0],
                   target_size[1] - int(round(float(oversize_bottom) / width_y * target_size[1]))
                   ]
                width_y = self.ds.RasterYSize - off_y

            if off_y < 0:
                oversize_top = -off_y
                tile_offset_top = int(float(oversize_top) / width_y * target_size[1])
                target_size = [
                   target_size[0], 
                   target_size[1] - int(float(oversize_top) / width_y * target_size[1]),
                   ]
                width_y = width_y + off_y
                off_y = 0

            bands = self.ds.RasterCount
            array = numpy.zeros((target_size[1]+1, target_size[0]+1, bands), numpy.uint8)
            for i in range(bands):
                array[:,:,i] = gdalarray.BandReadAsArray(self.ds.GetRasterBand(i+1), off_x, off_y, width_x, width_y, target_size[0]+1, target_size[1]+1)

            # generate transparancy/bgcolor mask
            if self.bgcolor[3] != 255:
                mask = None
                try:
                    masks = []
                    for i in range(bands):
                        masks.append(array[:,:,i] != self.bgcolor[i])
                    maskarray = numpy.logical_or.reduce(masks)*255
                    mask = PIL.Image.fromarray(maskarray).convert('L').convert('1')
#                    save_file("test_mask.png", mask)

                except Exception, e:
                    import traceback
                    traceback.print_exc()

            im = PIL.Image.fromarray(array)
#            save_file("test_im.png", im)

        big = PIL.Image.new("RGBA", tile.size(), self.bgcolor) 
        if im:
            target_size = map(int, target_size)
            im = im.crop((0, 0, target_size[0], target_size[1]))
            if mask:
                mask = mask.crop((0, 0, target_size[0], target_size[1]))
                big.paste(im, (tile_offset_left, tile_offset_top), mask=mask)
            else:
                big.paste(im, (tile_offset_left, tile_offset_top))

#        save_file("test_big.png", big)
        buffer = StringIO.StringIO()

        big.save(buffer, self.extension)

        buffer.seek(0)
        tile.data = buffer.read()
        return tile.data 
