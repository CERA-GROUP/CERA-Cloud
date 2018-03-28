# Copyright(c) 2010-2011 Carola Kaiser (ckaiser <at> cct.lsu.edu)
# Distributed under the Boost Software License, Version 1.0.
# See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)

from CeraCache.Layer import MetaLayer
from CeraCache.Service import TileCacheException

import osgeo.gdal as gdal
import osgeo.gdal_array as gdalarray
import numpy
import PIL
import os

def outside(bounds, extent):
    if extent is None:
        return True
    return bounds[2] < extent[0] or bounds[0] > extent[2] or \
           bounds[3] < extent[1] or bounds[1] > extent[3]

def inside(bounds, extent):
    if extent is None:
        return False
    return bounds[0] >= extent[0] and bounds[2] <= extent[2] and \
           bounds[1] >= extent[1] and bounds[3] <= extent[3]

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

def create_mask(bands, array, bgcolor):
    mask = None
    try:
        masks = []
        for i in range(bands):
            masks.append(array[:,:,i] != bgcolor[i])
        maskarray = numpy.logical_or.reduce(masks)*255
        mask = PIL.Image.fromarray(maskarray).convert('L').convert('1')
#        write_png('mask_%d.png' % index, mask)

    except Exception, e:
        import traceback
        traceback.print_exc()

    return mask

class GDALMosaic(MetaLayer):
    """
    The GDALMosaic Layer allows you to set up up to 3 overlapping GDAL
    datasources in TileCache.

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
      {'name':'file1', 'description': 'GDAL-readable file path, largest image.'},
      {'name':'file2', 'description': 'GDAL-readable file path, image overlapping file1.'},
      {'name':'file3', 'description': 'GDAL-readable file path, image overlapping file2.'},
      {'name':'bgcolor', 'description': 'background color for transparent pixels.', 'default': '0,0,0,0'},
      {'name':'altbgcolor', 'description': 'background color for non-existing tiles.', 'default': '0,0,0,0'},
    ] + MetaLayer.config_properties

    def fill(self, index):
        file = self.file[index]
        if file and os.path.exists(file):
            self.ds[index] = gdal.Open(file)
            self.geo_transform[index] = self.ds[index].GetGeoTransform()
            if self.geo_transform[index][2] != 0 or self.geo_transform[index][4] != 0:
                raise Exception("Image is not 'north-up', can not use.")
            if self.geo_transform[index] == (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
                self.geo_transform[index] = (0.0, 1.0, 0.0, self.ds[index].RasterYSize, 0.0, -1.0)
            size = [self.ds[index].RasterXSize, self.ds[index].RasterYSize]
            xform = self.geo_transform[index]
            self.data_extent[index] = [
               xform[0] + self.ds[index].RasterYSize * xform[2],
               xform[3] + self.ds[index].RasterYSize * xform[5],
               xform[0] + self.ds[index].RasterXSize * xform[1],
               xform[3] + self.ds[index].RasterXSize * xform[4]
            ]

    def fill_colors(self, index, bgcolor):
        bgcolor = map(int, bgcolor.split(','))
        if len(bgcolor) == 4:
            return (bgcolor[0], bgcolor[1], bgcolor[2], bgcolor[3])
        elif len(bgcolor) == 3:
            return (bgcolor[0], bgcolor[1], bgcolor[2], 255)
        raise TileCacheException("Bogus format for bgcolor.")

    def __init__ (self, name, file1 = None, file2 = None, file3 = None, 
            bgcolor = '0,0,0,0', altbgcolor = '0,0,0,0', **kwargs):

        # avoid scanning the directory before opening the file
        # see here for an explanation: https://trac.osgeo.org/gdal/ticket/2158
        gdal.SetConfigOption('GDAL_DISABLE_READDIR_ON_OPEN', 'TRUE')

        gdal.UseExceptions()
        MetaLayer.__init__(self, name, **kwargs)

        self.file = [file1, file2, file3]
        self.ds = [None, None, None]
        self.geo_transform = [None, None, None]
        self.bgcolor = [None, None, None, None]
        self.altbgcolor = [None, None, None, None]
        self.data_extent = [None, None, None]

        self.bgcolor[0] = self.fill_colors(0, bgcolor)
        self.bgcolor[1] = self.fill_colors(1, bgcolor)
        self.bgcolor[2] = self.fill_colors(2, bgcolor)

        if  (self.bgcolor[1] is not None and self.bgcolor[0] != self.bgcolor[1]) or \
                (self.bgcolor[2] is not None and self.bgcolor[0] != self.bgcolor[2]):
            raise TileCacheException("All images need same bgcolor (%s,%s,%s)" % (
                self.bgcolor[0], self.bgcolor[1], self.bgcolor[2]))

        self.altbgcolor[0] = self.fill_colors(0, altbgcolor)
        self.altbgcolor[1] = self.fill_colors(1, altbgcolor)
        self.altbgcolor[2] = self.fill_colors(2, altbgcolor)

        if  (self.altbgcolor[1] is not None and self.altbgcolor[0] != self.altbgcolor[1]) or \
                (self.altbgcolor[2] is not None and self.altbgcolor[0] != self.altbgcolor[2]):
            raise TileCacheException("All images need same altbgcolor (%s,%s,%s)" % (
                self.altbgcolor[0], self.altbgcolor[1], self.altbgcolor[2]))

    def renderTileHelper(self, index, tile, target = None):

        # if the file does not exists, just exit
        if self.ds[index] is None:
            return target

        import PIL.Image as PILImage

        bounds = tile.bounds()
        im = None
        mask = None
        altmask = None

        # If the image is entirely outside the bounds, don't bother doing anything with it:
        # just return None.
        if outside(bounds, self.data_extent[index]):
            return target

        tile_offset_left = tile_offset_top = 0

        target_size = tile.size()

        off_x = int((bounds[0] - self.geo_transform[index][0]) / self.geo_transform[index][1]);
        off_y = int((bounds[3] - self.geo_transform[index][3]) / self.geo_transform[index][5]);
        width_x = int(((bounds[2] - self.geo_transform[index][0]) / self.geo_transform[index][1]) - off_x);
        width_y = int(((bounds[1] - self.geo_transform[index][3]) / self.geo_transform[index][5]) - off_y);

        # Prevent from reading off the sides of an image
        if off_x + width_x > self.ds[index].RasterXSize:
            oversize_right = off_x + width_x - self.ds[index].RasterXSize
            target_size = [
                target_size[0] - int(float(oversize_right) / width_x * target_size[0]),
                target_size[1]
                ]
            width_x = self.ds[index].RasterXSize - off_x

        if off_x < 0:
            oversize_left = -off_x
            tile_offset_left = int(float(oversize_left) / width_x * target_size[0])
            target_size = [
                target_size[0] - int(float(oversize_left) / width_x * target_size[0]),
                target_size[1],
                ]
            width_x = width_x + off_x
            off_x = 0

        if off_y + width_y > self.ds[index].RasterYSize:
            oversize_bottom = off_y + width_y - self.ds[index].RasterYSize
            target_size = [
                target_size[0],
                target_size[1] - int(round(float(oversize_bottom) / width_y * target_size[1]))
                ]
            width_y = self.ds[index].RasterYSize - off_y

        if off_y < 0:
            oversize_top = -off_y
            tile_offset_top = int(float(oversize_top) / width_y * target_size[1])
            target_size = [
                target_size[0],
                target_size[1] - int(float(oversize_top) / width_y * target_size[1]),
                ]
            width_y = width_y + off_y
            off_y = 0

        bands = self.ds[index].RasterCount
        array = numpy.zeros((target_size[1]+1, target_size[0]+1, bands), numpy.uint8)
        for i in range(bands):
            a = gdalarray.BandReadAsArray(self.ds[index].GetRasterBand(i+1), \
                        off_x, off_y, width_x, width_y, target_size[0]+1, target_size[1]+1)
            if a is not None: array[:,:,i] = a

        # generate transparancy/bgcolor mask and altmask
        if self.bgcolor[index][3] != 255:
            mask = create_mask(bands, array, self.bgcolor[index])
            mask = mask.crop((0, 0, target_size[0], target_size[1]))
#            write_png('mask_%d.png' % index, mask)

        im = PIL.Image.fromarray(array)
#        write_png('image_%d.png' % index, im)

        if not target:
            target = PIL.Image.new("RGBA", tile.size(), self.bgcolor[index])

        target_size = map(int, target_size)
        im = im.crop((0, 0, target_size[0], target_size[1]))

        if index > 0 and mask is not None:
            # make all transparent areas in the pixel mask transparent in the
            # underlying image
            import PIL.ImageChops as PILImageChops

            alpha = target.split()[-1]
            alpha.paste(mask, (tile_offset_left, tile_offset_top), mask=PILImageChops.invert(mask))
            target.putalpha(alpha)
#            write_png('alpha_%d.png' % index, alpha)
        
            if self.altbgcolor[index][3] != 255:
                altmask = create_mask(bands, array, self.altbgcolor[index])
                altmask = altmask.crop((0, 0, target_size[0], target_size[1]))
#                write_png('altmask_%d.png' % index, PILImageChops.invert(altmask))

            if altmask is not None:
                im.paste(im, (0, 0), mask=altmask)
                mask.paste(altmask, (0, 0), PILImageChops.invert(altmask))
#                write_png('combinedmask_%d.png' % index, mask)

        # paste in higher resolution image
        target.paste(im, (tile_offset_left, tile_offset_top), mask=mask)
        return target

    def renderTile(self, tile):

        import StringIO
        import PIL.Image as PILImage

        if not self.ds[0]:
            self.fill(0)
        if not self.ds[1]:
            self.fill(1)
        if not self.ds[2]:
            self.fill(2)

        if not self.ds[0] and not self.ds[1] and not self.ds[2]:
            raise TileCacheException("GDAL datasource does not exist: %s." % self.file)

        bounds = tile.bounds()
#        if inside(bounds, self.data_extent[2]):
#            # fully inside innermost image
#            target = self.renderTileHelper(2, tile)
#            assert big is not None
#
#        elif inside(bounds, self.data_extent[1]):
#            # fully inside second image
#            target = self.renderTileHelper(1, tile)
#            assert target is not None
#
#            if not outside(bounds, self.data_extent[2]):
#                # overlapping innermost and second image
#                target = self.renderTileHelper(2, tile, target)
#                assert target is not None
#
#        else:

        #fallback
        target = self.renderTileHelper(0, tile)
        assert target is not None

        if not outside(bounds, self.data_extent[1]):
            # overlapping second image
            target = self.renderTileHelper(1, tile, target)
            assert target is not None

        if not outside(bounds, self.data_extent[2]):
            # overlapping innermost image
            target = self.renderTileHelper(2, tile, target)
            assert target is not None

        buffer = StringIO.StringIO()
        target.save(buffer, self.extension)

        buffer.seek(0)
        tile.data = buffer.read()
        return tile.data
