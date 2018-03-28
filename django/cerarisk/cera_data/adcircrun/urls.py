from django.conf.urls import url
from cera_data.adcircrun import views

urlpatterns = [

    url(r'^day=(?P<day>.*?)/time=(?P<time>.*?)/id=(?P<id>.*?)/yr=(?P<yr>.*?)/stormnr=(?P<stormnr>.*?)/adv=(?P<adv>.*?)/tracknr=(?P<tracknr>.*?)/tz=(?P<tz>.*?)/asgs=(?P<asgs>.*?)/dev=(?P<dev>.*?)/perm=(?P<perm>.*?)\.json$', views.getadcircrun),
#    url(r'^day=(?P<day>.*?)/time=(?P<time>.*?)/id=(?P<id>.*?)/yr=(?P<yr>.*?)/stormnr=(?P<stormnr>.*?)/adv=(?P<adv>.*?)/tracknr=(?P<tracknr>.*?)/tz=(?P<tz>.*?)/asgs=(?P<asgs>.*?)/dev=(?P<dev>.*?)\.json$', views.getadcircrun),
    url(r'^day=(?P<day>.*?)/time=(?P<time>.*?)/id=(?P<id>.*?)/yr=(?P<yr>.*?)/stormnr=(?P<stormnr>.*?)/adv=(?P<adv>.*?)/tracknr=(?P<tracknr>.*?)/tz=(?P<tz>.*?)/asgs=(?P<asgs>.*?)/dev=(?P<dev>.*?)\.json_redirect$', views.getadcircrun_redirect),
    url(r'^day=(?P<day>.*?)/time=(?P<time>.*?)/id=(?P<id>.*?)/stationid=(?P<stationid>[-A-Za-z0-9_]+)/cls=(?P<cls>\w*)/tz=(?P<tz>\w*)/unit=(?P<unit>\w*)/data_host=(?P<data_host>.*?)/dev=(?P<dev>.*?)\.html$', views.gethydro),
    url(r'^day=(?P<day>.*?)/time=(?P<time>.*?)/id=(?P<id>.*?)/stationid=(?P<stationid>[-A-Za-z0-9_]+)/tz=(?P<tz>\w*)/data_host=(?P<data_host>.*?)\.html$', views.getprec),
    url(r'^day=(?P<day>.*?)/time=(?P<time>.*?)/id=(?P<id>.*?)/queryid=(?P<queryid>\w*)/query=(?P<query>\w*)/layer=(?P<layer>\w*)/timestep=(?P<timestep>\w*)/tz=(?P<tz>\w*)/unit=(?P<unit>\w*)/data_host=(?P<data_host>.*?)\.html$', views.getquery),
    url(r'^id=(?P<id>.*?)/tz=(?P<tz>.*?)/asgs=(?P<asgs>.*?)\.hdstorm$', views.getheaderstorm),
    url(r'^id=(?P<id>.*?)/tz=(?P<tz>.*?)/asgs=(?P<asgs>.*?)\.hd$', views.getheader),
    url(r'^id=(?P<id>.*?)/asgs=(?P<asgs>.*?)\.hdremark$', views.getheader_remark),
    url(r'^id=(?P<id>.*?)/tz=(?P<tz>.*?)/layer=(?P<layer>.*?)/dev=(?P<dev>.*?)/unit=(?P<unit>.*?)\.html$', views.getlegend),
    url(r'^id=(?P<id>.*?)/tz=(?P<tz>.*?)/layer=(?P<layer>.*?)/dev=(?P<dev>.*?)/unit=(?P<unit>.*?)\.html_redirect$', views.getlegend_redirect),
    url(r'^id=(?P<id>.*?)/dev=(?P<dev>.*?)/asgs=(?P<asgs>.*?)\.desc$', views.getadcircrundesc),

    # filter_ceraserver by adcirchost
    url(r'^adcirchost=(?P<adcirchost>.*?)/cerahost=(?P<cerahost>.*?)\.html$', views.filter_cera_server),
    # filter_asgs
    url(r'^grid=(?P<grid>.*?)/track=(?P<track>.*?)\.html$', views.filter_asgs_runs),
    # filter_cera_workflow (pub or pro run)
    url(r'^adcirchost=(?P<adcirchost>.*?)/cerahost=(?P<cerahost>.*?)\.workflow$', views.filter_cera_workflow),

    # query outside domain
    url(r'^query_outsidedomain$', views.outsidedomain),

    #filldb_create_id
    url(r'^daytime=(?P<daytime>.*?)/daytimecera=(?P<daytimecera>.*?)/end=(?P<end>.*?)/grid=(?P<grid>.*?)/windmodel=(?P<windmodel>.*?)/surfheight=(?P<surfheight>.*?)/h0=(?P<h0>.*?)/msboundflux=(?P<msboundflux>.*?)/msboundid=(?P<msboundid>.*?)/atboundflux=(?P<atboundflux>.*?)/atboundid=(?P<atboundid>.*?)/asgsinst=(?P<asgsinst>.*?)/adcirchost=(?P<adcirchost>.*?)/ncpu=(?P<ncpu>.*?)/trackid=(?P<trackid>.*?)/audience=(?P<audience>.*?)/pub=(?P<pub>.*?)\.filldb$', views.filldb_id),
    #filldb_asgs
    url(r'^id=(?P<id>.*?)/asgs=(?P<asgs>.*?)/audience=(?P<audience>.*?)/globmesh=(?P<globmesh>.*?)/pub=(?P<pub>.*?)\.filldb$', views.filldb_asgs),
    #filldb_website_region
    url(r'^id=(?P<id>.*?)/orig_asgs=(?P<orig_asgs>.*?)/globmesh=(?P<globmesh>.*?)\.filldb$', views.filldb_website_region),
    #filldb_layer_info
    url(r'^id=(?P<id>.*?)/layer=(?P<layer>.*?)/wmsserver=(?P<wmsserver>.*?)\.filldb$', views.filldb_data),
    #filldb_storminfo
    url(r'^year=(?P<year>.*?)/stormnr=(?P<stormnr>.*?)/stormname=(?P<stormname>.*?)/firstadv=(?P<firstadv>.*?)/adv=(?P<adv>.*?)/stormcls=(?P<stormcls>.*?)/cat=(?P<cat>.*?)/tracknr=(?P<tracknr>.*?)/percent=(?P<percent>.*?)/advtime=(?P<advtime>.*?)\.filldb$', views.filldb_storm),
    #filldb_lastadv
    url(r'^trackid=(?P<trackid>.*?)/lastadv=(?P<lastadv>.*?)\.filldb$', views.filldb_lastadv),
    #filldb_subtrack
    url(r'^id=(?P<id>.*?)/trackid=(?P<trackid>.*?)\.filldb$', views.filldb_subtrack),

    # check default_view
    url(r'^id=(?P<id>.*?)\.default_view$', views.check_default_view),

# emails
    # emailtext no storm
    url(r'^id=(?P<id>.*?)/asgs=(?P<asgs>.*?)\.emailtext$', views.emailtext_nostorm),
    # emailsubject no storm
    url(r'^id=(?P<id>.*?)/asgs=(?P<asgs>.*?)\.emailsubject$', views.emailsubject_nostorm),
    # emailtext storm
    url(r'^id=(?P<id>.*?)/asgs=(?P<asgs>.*?)/rapid=(?P<rapid>.*?)\.emailtextstorm$', views.emailtext_storm),
    # emailsubject storm
    url(r'^id=(?P<id>.*?)/asgs=(?P<asgs>.*?)/rapid=(?P<rapid>.*?)\.emailsubjectstorm$', views.emailsubject_storm),

# parse xml for invests and create jQuery template for trackpoint tooltips
    url(r'^id=(?P<id>.*?)/investnr=(?P<investnr>.*?)/perc=(?P<perc>.*?)/cat=(?P<cat>.*?)\.invest$', views.parse_invest),
    url(r'^id=(?P<trackid>.*?)\.trackpt$', views.create_tooltip_trackpoint),

# legend images
    url(r'^id=(?P<id>.*?)/layer=(?P<layer>.*?)\.legend$', views.getlegendimg),

# test urls
    url(r'^day=(?P<day>.*?)/time=(?P<time>.*?)/id=(?P<id>.*?)/tz=(?P<tz>.*?)/asgs=(?P<asgs>.*?)\.test$', views.test_retrieve_adcrun_infos),
    url(r'^day=(?P<day>.*?)/tz=(?P<tz>.*?)/asgs=(?P<asgs>.*?)\.test$', views.test_retrieve_adcrun_days),
    url(r'^year=(?P<year>.*?)/stormnr=(?P<stormnr>.*?)/adv=(?P<adv>.*?)/tracknr=(?P<tracknr>.*?)/tz=(?P<tz>.*?)/asgs=(?P<asgs>.*?)\.test$', views.test_retrieve_alltracks),
    url(r'^year=(?P<year>.*?)/stormnr=(?P<stormnr>.*?)/asgs=(?P<asgs>.*?)\.test$', views.test_retrieve_allstorms),
    url(r'^year=(?P<year>.*?)/asgs=(?P<asgs>.*?)\.test$', views.test_retrieve_adcrun_years)

]

