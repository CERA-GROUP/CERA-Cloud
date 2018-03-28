from django.conf.urls import *
from django.views.decorators.cache import cache_page
from cera_data.ceracgi import cera_wms_tiled, cera_ani_tiled, cera_cgi, timesteps_forwarding, cera_wfs_forwarding

# urls used for former cgi services
urlpatterns = [ #patterns('cera_data.ceracgi',
#    (r'cera_wms_tiled', cache_page(3600 * 24)(cera_wms_tiled.do_work)),
    url(r'cera_wms_tiled', cera_wms_tiled.do_work),
#    (r'cera_ani_tiled', cache_page(3600 * 24)(cera_ani_tiled.do_work)),
    url(r'cera_ani_tiled', cera_ani_tiled.do_work),
    url(r'cera_cgi', cera_cgi.do_generate_cera_html_dev),
    url(r'cera_nc_cgi', cera_cgi.do_generate_cera_html_nc),
    url(r'cera_ng_cgi', cera_cgi.do_generate_cera_html_ng),
    url(r'cera_ri_cgi', cera_cgi.do_generate_cera_html_ri),
    url(r'cera_timesteps_cgi', timesteps_forwarding.do_work),
#    (r'cera_wfs_cgi', 'cera_wfs_cgi.do_work'),
    url(r'cera_wfs', cera_wfs_forwarding.do_work)
#    (r'(?P<filename>.*?)', 'cera_wms_tiled.do_work')
]


