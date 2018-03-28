# BSD Licensed, Copyright (c) 2006-2008 MetaCarta, Inc.

from CeraCache.Service import Request, Capabilities
from CeraCache.Services.WMS import WMS
import CeraCache.Layer as Layer
import copy
import math

def get_param(fields, key, dflt = None):
    if fields.has_key(key):
        return fields[key]
    elif fields.has_key(key.upper()):
        return fields[key.upper()]
    return dflt

defaults = {
    'service': 'WMS',
    'version': '1.1.1',
    'format': 'image/png',
    'bgcolor': '0xFFFFFFFF',
    'srs': 'EPSG:4326',
    'width': '256',
    'height':'256',
    'transparent': 'true',
    'reaspect': 'false'
}

keys_to_remove = [
    'metatileexact', 'metasize',
    'y', 'm', 'd', 't',
    'wms_dir', 'wms_host',
    'cache_only', 'cache_dir_web',
    'width', 'height', 'zoom'
]

class KML(WMS):
    def parse (self, fields, path, host):
        wmsfields = copy.deepcopy(fields)

        # replace request type
        if wmsfields.has_key('request'):
            wmsfields['request'] = 'GetMap'
        else:
            wmsfields['REQUEST'] = 'GetMap'

        # generate proper styles='...' (based on number of layers
        layers = get_param(fields, 'layers', '').split(',')
        wmsfields['styles'] = ','.join(['default' for l in layers])

        # add missing keys using the defaults from above
        for d in defaults.keys():
            if not fields.has_key(d) and not fields.has_key(d.upper()):
                wmsfields[d] = defaults[d]

        # extract width and height of image if this is a top level kml
        name = get_param(fields, 'name', '')
        width = int(get_param(fields, 'width', '0'))
        if width != 0:
            if len(name) == 0:
                name = 'CERA'
            # altidute calculation taken from here:
            # http://throwless.wordpress.com/2008/03/06/zoom-level-finding-the-right-one/
            height = int(get_param(fields, 'height', '0'))
            zoom = int(get_param(fields, 'zoom', '0'))
            lookat_bbox = get_param(wmsfields, 'bbox')
            altitude = (math.pow(2, 18-zoom) * math.sqrt(width*width+height*height)) / 3.3
            b = map(float, lookat_bbox.split(','))
            lookat = """
    <name>%s</name>
    <LookAt>
      <longitude>%f</longitude>
      <latitude>%f</latitude>
      <altitude>%f</altitude>
      <altitudeMode>absolute</altitudeMode>
      <tilt>0</tilt>
    </LookAt>
    <Style>
      <ListStyle>
        <listItemType>checkHideChildren</listItemType>
      </ListStyle>
    </Style>""" % (name, (b[0] + b[2])/2, (b[1] + b[3])/2, altitude)
            if wmsfields.has_key('bbox'):
                wmsfields['bbox'] = '-180,0,0,85.0511287798066'
            else:
                wmsfields['BBOX'] = '-180,0,0,85.0511287798066'
        else:
            lookat = ''

        # retrieve the tile(s) from the cache
        try:
            tile = WMS.parse(self, wmsfields, path, host)
            if type(tile) == type([]):
                tile = tile[0]
        except:
            # any error causes an empty kml file to be returned
            kml = '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://earth.google.com/kml/2.1"></kml>'
            return ("application/vnd.google-earth.kml+xml", kml)

        # remove certain keys from WMS url
        for k in keys_to_remove:
            if wmsfields.has_key(k):
                wmsfields.pop(k)
            elif wmsfields.has_key(k.upper()):
                wmsfields.pop(k.upper())

            if fields.has_key(k):
                fields.pop(k)
            elif fields.has_key(k.upper()):
                fields.pop(k.upper())

        # now generatethe requested kml
        kml = self.generate_kml_doc(tile, fields, wmsfields, path, lookat,
                                    base_path=host)
        return ("application/vnd.google-earth.kml+xml", kml)

    def generate_kml_doc(self, tile, fields, wmsfields, path, lookat,
                         base_path="", include_wrapper = True):
        tiles = [
            Layer.Tile(tile.layer, 2*tile.x,     2*tile.y, tile.z + 1),
            Layer.Tile(tile.layer, 2*tile.x + 1, 2*tile.y, tile.z + 1),
            Layer.Tile(tile.layer, 2*tile.x + 1, 2*tile.y + 1, tile.z + 1),
            Layer.Tile(tile.layer, 2*tile.x ,    2*tile.y + 1, tile.z + 1)
        ]

        # create the sub-kml entries
        network_links = []
        for single_tile in tiles:
            if single_tile.z >= tile.layer.levels:
                continue
            b = single_tile.bounds()
            bbox = "%s,%s,%s,%s" % (b[0], b[1], b[2], b[3])
            if fields.has_key('bbox'):
                fields['bbox'] = bbox
            else:
                fields['BBOX'] = bbox

            network_links.append("""    <NetworkLink>
      <name>tile</name>
      <Region>
        <Lod>
          <minLodPixels>128</minLodPixels><maxLodPixels>-1</maxLodPixels>
        </Lod>
        <LatLonAltBox>
          <north>%s</north>
          <south>%s</south>
          <east>%s</east>
          <west>%s</west>
        </LatLonAltBox>
      </Region>
      <Link>
        <href><![CDATA[%s?%s]]></href>
        <viewRefreshMode>onRegion</viewRefreshMode>
      </Link>
    </NetworkLink>""" % (b[3], b[1], b[2], b[0], base_path, \
        '&'.join(["%s=%s" % (k, fields[k]) for k in fields])))

        b = tile.bounds()
        kml = []
        if include_wrapper:
            kml.append( """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.1">
  <!-- Copyright (c) 2012-2013 CERA Group, Louisiana State University -->
  <!-- See http://www.coastalemergency.org for more information. -->
  <Document>""")

        if tile.z == 2:
            min_lod_pixels = -1
        else:
            min_lod_pixels = 128
        if tile.z == tile.layer.levels - 1:
            max_lod_pixels = -1
        else:
            max_lod_pixels = 768

        # append the actual tile url
        kml.append("""    <Region>
      <Lod>
        <minLodPixels>%d</minLodPixels><maxLodPixels>%d</maxLodPixels>
      </Lod>
      <LatLonAltBox>
        <north>%s</north>
        <south>%s</south>
        <east>%s</east>
        <west>%s</west>
      </LatLonAltBox>
    </Region>
    <GroundOverlay>
      <drawOrder>%s</drawOrder>
      <Icon>
        <href><![CDATA[%s?%s]]></href>
      </Icon>
      <LatLonBox>
        <north>%s</north>
        <south>%s</south>
        <east>%s</east>
        <west>%s</west>
      </LatLonBox>
    </GroundOverlay>%s
%s""" % (min_lod_pixels, max_lod_pixels, b[3], b[1], b[2], b[0], tile.z, base_path, \
            '&'.join(["%s=%s" % (k, v) for k, v in wmsfields.iteritems()]), \
            b[3], b[1], b[2], b[0], lookat, "\n".join(network_links)))

        if include_wrapper:
            kml.append("""  </Document>\n</kml>\n""" )

        kml = "\n".join(kml)
        return kml
