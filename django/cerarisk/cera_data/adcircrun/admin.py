from pytz import timezone, utc
from datetime import datetime
from django.utils import dateformat
from string import replace

from cera_data.adcircrun.models import *
from cera_data.settings import CERA_ENV

from django.contrib import admin
from django.forms import ModelForm

###################################################################
# display times in UTC in django admin (default is Central)
def as_timezone(dt, tz):
     if dt is not None:
         dt = dt.astimezone(tz)
         return tz.normalize(dt)
     return None

###################################################################
# display datetime fields in UTC (only for readibility)
def adcrun_daytime(obj):
    d = as_timezone(obj.adcrun_info.adcrun_daytime_utc, utc)
    if d is not None:
        dt = d.strftime('%Y-%m-%d %H:%M')
        return dt
    return None
adcrun_daytime.short_description = 'start time (UTC) '

# convert Foreign key elements to strings
def adcrunid(obj):
    return ("%s" % obj.adcrun_info.id)
adcrunid.short_description = 'ID adcrun_info'

#def storm_name(obj):
#    return ("%s #%s" % (obj.adcrun_info.track_id.advisory.storm.stormname, obj.adcrun_info.track_id.advisory.advisory))

###################################################################
# display datetime fields in UTC (only for readibility)
def adcrun_daytime(obj):
    d = as_timezone(obj.adcrun_daytime_utc, utc)
    if d is not None:
        dt = d.strftime('%Y-%m-%d %H:%M')
        return dt
    return None
adcrun_daytime.short_description = 'Start time'

def adcrun_daytimecera(obj):
    d = as_timezone(obj.adcrun_daytime_cera, utc)
    if d is not None:
        dt = d.strftime('%Y-%m-%d %H:%M')
        return dt
    return None
adcrun_daytimecera.short_description = 'CERA time'

def adcrun_timecera(obj): # for display site
    d = as_timezone(obj.adcrun_daytime_cera, utc)
    if d is not None:
        dt = d.strftime('%H:%M')
        return dt
    return None
adcrun_timecera.short_description = 'CERA time'

def adcrun_enddaytime(obj):
    d = as_timezone(obj.adcrun_enddaytime_utc, utc)
    if d is not None:
        dt = d.strftime('%Y-%m-%d %H:%M')
        return dt
    return None
adcrun_enddaytime.short_description = 'End time'

def asgs_system(obj):
    s = []
    if obj.asgs_dev:
        s.append("dev")
    if obj.asgs_pro:
        s.append("pro")
    if obj.asgs_pub:
        s.append("pub")
    if obj.asgs_nc:
        s.append("nc")
    if obj.asgs_ng:
        s.append("ng")
    if obj.asgs_pr:
        s.append("pr")
    if obj.asgs_ri:
        s.append("ri")
    if obj.asgs_st:
        s.append("st")
    return " ".join(s)
asgs_system.short_description = 'ASGS'

def website_region(obj):
    if obj.website_region:
        return obj.website_region
website_region.short_description = 'Region'

###################################################################
def storm_name(obj):
    if (obj.track_id) > 0:
        if (obj.enable_adminmode) or (obj.enable_public):
            if obj.track_id.mod_percent == "0":
                return ("%s #%s %s" % (obj.track_id.advisory.storm.stormname, obj.track_id.advisory.advisory, obj.track_id.track))
            else:
                return ("%s #%s %s %s" % (obj.track_id.advisory.storm.stormname, obj.track_id.advisory.advisory, obj.track_id.track, obj.track_id.mod_percent))
        else:
            if obj.track_id.mod_percent == "0":
                return ("%s #%s %s (disabled)" % (obj.track_id.advisory.storm.stormname, obj.track_id.advisory.advisory, obj.track_id.track))
            else:
                return ("%s #%s %s %s (disabled)" % (obj.track_id.advisory.storm.stormname, obj.track_id.advisory.advisory, obj.track_id.track, obj.track_id.mod_percent))
    else:
        if not (obj.enable_adminmode) and not (obj.enable_public):
            return ("(None) (disabled)")

def track_id(obj):
    if (obj.track_id) > 0:
        return ("%s" % obj.track_id.id)

class layerinfoInline(admin.TabularInline):
    model = layerinfo
    extra = 0
    fields = ['layername', 'show_layer']

class subtrackInline(admin.TabularInline):
    model = subtrack
    extra = 0
    fields = ['trackid']

class adcrun_infoAdmin(admin.ModelAdmin):
    save_on_top = True
#    change_list_template = "/django/%s/templates/admin/change_list.html" % CERA_ENV['DJANGO_ADMIN_PATH']

    model = adcrun_info
    inlines = [subtrackInline, layerinfoInline]
    fields = ['adcrun_daytime_utc', adcrun_daytime, 'adcrun_daytime_cera', adcrun_daytimecera, 'adcrun_enddaytime_utc', adcrun_enddaytime,
              'grid',  'grid_datum', 'legend', 'windmodel', 'has_adv', 'track_id',
              ('enable_adminmode', 'enable_public'), ('asgs_dev', 'asgs_pro', 'asgs_pub', 'asgs_nc', 'asgs_ng', 'asgs_pr', 'asgs_ri', 'asgs_st'),
	      'website_region',
              ('default_view', 'is_pseudo'), 'sequence_nr', 'wmsserver', 'nr_cacheserver', 'program_version',
              'description',  'remark',
              'adcirc_datahost', 'asgs_instance', 'ncpu',
              'surfheight', 'h0', 'msboundflux', 'msboundid', 'atboundflux', 'atboundid'
              ]

    # display of add/change page
    list_display = ('id', adcrun_daytime, adcrun_timecera, asgs_system, website_region, storm_name, 'default_view', 'grid', 'windmodel', 'wmsserver', 'asgs_instance', 'adcirc_datahost', 'is_pseudo', 'remark')
    readonly_fields = (adcrun_daytime, adcrun_enddaytime, adcrun_daytimecera)
    #list_filter = ('adcrun_daytime_utc', 'grid')

###################################################################
# display on 'Advisories' admin page, e.g. '2010 Earl #31'
# obj.advisory uses defined __unicode__
# display datetime fields in UTC (only for readibility)
def adv_utc(obj):
    a = as_timezone(obj.adv_time_utc, utc)
    if a is not None:
        ad = a.strftime('%Y-%m-%d %H:%M')
        return ad
    return None
adv_utc.short_description = 'NHC advisory time (UTC)'

def advisory_name(obj):
    return ("%s #%s" % (obj.storm, obj.advisory))

class trackInline(admin.TabularInline):
    model = track
    extra = 0
    fields = ['track', 'mod_percent', 'has_model_run', \
             ('dependent_asgs_pro', 'dependent_asgs_pub', 'dependent_asgs_ng', 'dependent_asgs_nc'), \
             ('dependent_asgs_dev', 'dependent_asgs_pr', 'dependent_asgs_ri', 'dependent_asgs_st'), \
             ('dependent_region_nc_ng', 'dependent_region_nc', 'dependent_region_ng'), ('dependent_region_pr', 'dependent_region_ri'), \
             ('dependent_enable_public_pro', 'dependent_enable_public_pub', 'dependent_enable_public_ng', 'dependent_enable_public_nc'), \
             ('dependent_enable_public_dev', 'dependent_enable_public_pr', 'dependent_enable_public_ri', 'dependent_enable_public_st')]
    readonly_fields = ('has_model_run', 'dependent_asgs_pro', 'dependent_asgs_pub', 'dependent_asgs_ng', 'dependent_asgs_nc', \
             'dependent_asgs_dev', 'dependent_asgs_pr', 'dependent_asgs_ri', 'dependent_asgs_st', \
             'dependent_region_nc_ng', 'dependent_region_nc', 'dependent_region_ng', 'dependent_region_pr', 'dependent_region_ri', \
             'dependent_enable_public_dev', 'dependent_enable_public_pro', 'dependent_enable_public_pub', 'dependent_enable_public_nc', \
             'dependent_enable_public_ng', 'dependent_enable_public_pr', 'dependent_enable_public_ri', 'dependent_enable_public_st')

class advisoryAdmin(admin.ModelAdmin):
    save_on_top = True
#    change_list_template = "/django/%s/templates/admin/change_list.html" % CERA_ENV['DJANGO_ADMIN_PATH']

    model = advisory
    inlines = [trackInline]
    fieldsets = [
        (None,       {'fields': ['storm']}),
        ('Advisory', {'fields': ['advisory', 'stormclass', 'category', 'adv_time_utc', adv_utc, \
                     ('dependent_asgs_pro', 'dependent_asgs_pub', 'dependent_asgs_ng', 'dependent_asgs_nc'), \
                     ('dependent_asgs_dev', 'dependent_asgs_pr', 'dependent_asgs_ri', 'dependent_asgs_st'), \
                     ('dependent_region_nc_ng', 'dependent_region_nc', 'dependent_region_ng'), ('dependent_region_pr', 'dependent_region_ri'), \
                     ('dependent_enable_public_pro', 'dependent_enable_public_pub', 'dependent_enable_public_nc', 'dependent_enable_public_ng'), \
                     ('dependent_enable_public_dev', 'dependent_enable_public_pr', 'dependent_enable_public_ri', 'dependent_enable_public_st')]}),
    ]
    # display of add/change page
    list_display = (advisory_name, 'adv_time_utc', adv_utc)
    readonly_fields = (adv_utc, 'dependent_asgs_pro', 'dependent_asgs_pub', 'dependent_asgs_ng', 'dependent_asgs_nc', \
             'dependent_asgs_dev', 'dependent_asgs_pr', 'dependent_asgs_ri', 'dependent_asgs_st', \
             'dependent_region_nc_ng', 'dependent_region_nc', 'dependent_region_ng', 'dependent_region_pr', 'dependent_region_ri', \
             'dependent_enable_public_dev', 'dependent_enable_public_pro', 'dependent_enable_public_pub', 'dependent_enable_public_nc', \
             'dependent_enable_public_ng', 'dependent_enable_public_pr', 'dependent_enable_public_ri', 'dependent_enable_public_st')

###################################################################
# display datetime fields in UTC (only for readibility)
def first_utc(obj):
    s = as_timezone(obj.start_date_utc, utc)
    if s is not None:
        st = s.strftime('%Y-%m-%d %H:%M')
        return st
    return None
first_utc.short_description = 'First NHC advisory (UTC)'

def last_utc(obj):
    l = as_timezone(obj.last_date_utc, utc)
    if l is not None:
        lt = l.strftime('%Y-%m-%d %H:%M')
        return lt
    return None
last_utc.short_description = 'Last NHC advisory (UTC)'

def storm_name(obj):
    return ("%s #%s" % (obj.year, obj.stormname))

class stormAdmin(admin.ModelAdmin):
    model = storm
    fields = ['year', 'storm_number', 'stormname', 'start_date_utc', first_utc, 'last_date_utc', last_utc, 'has_hindcast', \
             ('dependent_asgs_pro', 'dependent_asgs_pub', 'dependent_asgs_ng', 'dependent_asgs_nc'), \
             ('dependent_asgs_dev', 'dependent_asgs_pr', 'dependent_asgs_ri', 'dependent_asgs_st'), \
             ('dependent_region_nc_ng', 'dependent_region_nc', 'dependent_region_ng'), ('dependent_region_pr', 'dependent_region_ri'), \
             ('dependent_enable_public_pro', 'dependent_enable_public_pub', 'dependent_enable_public_ng', 'dependent_enable_public_nc'), \
             ('dependent_enable_public_dev', 'dependent_enable_public_pr', 'dependent_enable_public_ri', 'dependent_enable_public_st')
    ]
    # display of add/change page
    list_display = (storm_name, 'start_date_utc', first_utc)
    readonly_fields = (first_utc, last_utc, 'dependent_asgs_pro', 'dependent_asgs_pub', 'dependent_asgs_ng', 'dependent_asgs_nc', \
             'dependent_asgs_dev', 'dependent_asgs_pr', 'dependent_asgs_ri', 'dependent_asgs_st', \
             'dependent_region_nc_ng', 'dependent_region_nc', 'dependent_region_ng', 'dependent_region_pr', 'dependent_region_ri', \
             'dependent_enable_public_dev', 'dependent_enable_public_pro', 'dependent_enable_public_pub', 'dependent_enable_public_nc', \
             'dependent_enable_public_ng', 'dependent_enable_public_pr', 'dependent_enable_public_ri', 'dependent_enable_public_st')

###################################################################
# assign CERA servers to ADCIRC hosts +
# decides whether the complete CERA worklow (for nc_ng/pro) or the limited workflow (pub) will be executed on the given CERA server -> cera.process.py 
class filter_ceraserverAdmin(admin.ModelAdmin):
    model = filter_ceraserver
    fields = ['cera_datahost', 'adcirc_datahost', 'active', 'pro_model_run']
    # display of add/change page
    list_display = ('cera_datahost', 'adcirc_datahost', 'active', 'pro_model_run')

###################################################################
# filter execution of ASGS runs by mesh and track
class filter_asgsAdmin(admin.ModelAdmin):
    model = filter_asgs
    fields = ['grid', 'default_view_ng', 'default_view_nc', 'default_view_pro', 'daily', 'stormt01', 'stormt02', 'stormt03', 'stormt04', 'stormt05', 'stormt06', 'stormt07', 'stormt08', 'stormt14', 'stormt15', 'stormt88']
    # display of add/change page
    list_display = ('grid', 'default_view_ng', 'default_view_nc','default_view_pro',  'daily', 'stormt01', 'stormt02', 'stormt03', 'stormt04', 'stormt05', 'stormt06', 'stormt07', 'stormt08', 'stormt14', 'stormt15', 'stormt88')
    # readonly_fields = (first_utc,last_utc)

###################################################################
class storm_yearAdmin(admin.ModelAdmin):
    model = storm_year
    fields = ['year', ('dependent_asgs_pro', 'dependent_asgs_pub', 'dependent_asgs_ng', 'dependent_asgs_nc'), \
             ('dependent_asgs_dev', 'dependent_asgs_pr', 'dependent_asgs_ri', 'dependent_asgs_st'), \
             ('dependent_region_nc_ng', 'dependent_region_nc', 'dependent_region_ng'), ('dependent_region_pr', 'dependent_region_ri'), \
             ('dependent_enable_public_pro', 'dependent_enable_public_pub', 'dependent_enable_public_ng', 'dependent_enable_public_nc'), \
             ('dependent_enable_public_dev', 'dependent_enable_public_pr', 'dependent_enable_public_ri', 'dependent_enable_public_st')
    ]
    readonly_fields = ('dependent_asgs_pro', 'dependent_asgs_pub', 'dependent_asgs_ng', 'dependent_asgs_nc', \
             'dependent_asgs_dev', 'dependent_asgs_pr', 'dependent_asgs_ri', 'dependent_asgs_st', \
             'dependent_region_nc_ng', 'dependent_region_nc', 'dependent_region_ng', 'dependent_region_pr', 'dependent_region_ri', \
             'dependent_enable_public_dev', 'dependent_enable_public_pro', 'dependent_enable_public_pub', 'dependent_enable_public_nc', \
             'dependent_enable_public_ng', 'dependent_enable_public_pr', 'dependent_enable_public_ri', 'dependent_enable_public_st')

###################################################################
def user_name(obj):
    return "%s %s" % (obj.user.first_name, obj.user.last_name)
user_name.short_description = 'Name'

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', user_name, 'cera')

####################################################################
admin.site.register(adcrun_info, adcrun_infoAdmin)
admin.site.register(storm_year, storm_yearAdmin)
admin.site.register(storm, stormAdmin)
admin.site.register(advisory,advisoryAdmin)
admin.site.register(filter_asgs,filter_asgsAdmin)
admin.site.register(filter_ceraserver,filter_ceraserverAdmin)
#admin.site.unregister(UserProfile)
admin.site.register(UserProfile, UserProfileAdmin)