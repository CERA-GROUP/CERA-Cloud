import os, httplib, urllib
import pytz

from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse
# from django.views.decorators.cache import cache_page

from datetime import datetime, time, timedelta
from cera_data.adcircrun.models import *
from cera_define import *
from django.db.models.signals import pre_save
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError

from xml.dom import minidom
from cera_data.settings import CERA_ENV

###############################################################################
def getenv(d, key, deflt):
  if d.has_key(key):
    return d[key]
  return deflt

###############################################################################
# get pytz timezone from descriptive short name
def get_pytz_timezone(tz):

    tz = tz.upper()
    if tz == 'CDT' or tz == 'CST':
        return pytz.timezone('US/Central')

    if tz == 'EDT' or tz == 'EST':
        return pytz.timezone('US/Eastern')

    if tz == 'AST': # no daylight savings for AST
        return pytz.timezone('America/Puerto_Rico')

    return pytz.utc

##############################################################################
def as_timezone(dt, tz):
    dt = dt.astimezone(tz)
    return tz.normalize(dt)

##############################################################################
class adcrun_day_proxy:
    __slots__ = [ 'adcrun_day', 'has_adv' ]

    def __init__(self, day, has_adv):
        self.adcrun_day = day
        self.has_adv = has_adv

##############################################################################
# handle non-authenticated users
def filter_allinfos_asgs_pub(allinfos, asgs):
    return allinfos.filter(asgs_pub=True)

# handle users that are authenticated as 'nc_ng'
def filter_allinfos_asgs_ncng(allinfos, asgs):

    from django.db.models import Q
    if asgs == 'nc':
        return allinfos.filter(asgs_nc=True)
    if asgs == 'ng':
        return allinfos.filter(asgs_ng=True)

    return allinfos.filter(Q(asgs_ng=True) | Q(asgs_nc=True))

# handle users that are authenticated as 'pro'
def filter_allinfos_asgs_pro(allinfos, asgs):

    from django.db.models import Q
    allinfos = allinfos.filter(Q(asgs_pro=True) | Q(asgs_ng=True) | Q(asgs_nc=True))

    if asgs == 'nc':
        return allinfos.filter(Q(website_region='nc_ng') | Q(website_region='nc'))
    if asgs == 'ng':
        return allinfos.filter(Q(website_region='nc_ng') | Q(website_region='ng'))

    return allinfos.filter(Q(website_region='nc_ng') | Q(website_region='nc') | Q(website_region='ng'))

# filter all available runs based on asgs system and user authentication
def filter_allinfos_asgs(perm, allinfos, asgs):

    if len(asgs) == 0:
        return allinfos.filter(asgs_pub=True)

    if asgs == 'pl':
        # ISAAC hindcast only
        return allinfos.filter(id=7596)

    if asgs == 'pr':
        return allinfos.filter(asgs_pr=True)
    if asgs == 'ri':
        return allinfos.filter(asgs_ri=True)
    if asgs == 'st':
        return allinfos.filter(asgs_st=True)
    if asgs == 'dev':
        return allinfos.filter(asgs_dev=True)

    if perm == 'pro':
        return filter_allinfos_asgs_pro(allinfos, asgs)

    if perm == 'nc_ng':
        return filter_allinfos_asgs_ncng(allinfos, asgs)

    return filter_allinfos_asgs_pub(allinfos, asgs)

##############################################################################
def filter_data_by_asgs_pub(perm, data, asgs, adminmode):
    data = data.filter(dependent_enable_adminmode_pub=True)
    if not adminmode:
        data = data.filter(dependent_enable_public_pub=True)
    return data.filter(dependent_asgs_pub=True)

def filter_data_by_asgs_ncng(perm, data, asgs, adminmode):

    if asgs == 'nc':
        data = data.filter(dependent_enable_adminmode_nc=True)
        if not adminmode:
            data = data.filter(dependent_enable_public_nc=True)
        return data.filter(dependent_asgs_nc=True)

    if asgs == 'ng':
        data = data.filter(dependent_enable_adminmode_ng=True)
        if not adminmode:
            data = data.filter(dependent_enable_public_ng=True)
        return data.filter(dependent_asgs_ng=True)

    from django.db.models import Q
    data = data.filter( \
        Q(dependent_enable_adminmode_nc=True) | \
        Q(dependent_enable_adminmode_ng=True))
    if not adminmode:
        data = data.filter( \
            Q(dependent_enable_public_nc=True) | \
            Q(dependent_enable_public_ng=True))
    return data.filter( \
        Q(dependent_asgs_nc=True) | \
        Q(dependent_asgs_ng=True))

def filter_data_by_asgs_pro(perm, data, asgs, adminmode):

    from django.db.models import Q
    data = data.filter( \
        Q(dependent_enable_adminmode_pro=True) | \
        Q(dependent_enable_adminmode_nc=True) | \
        Q(dependent_enable_adminmode_ng=True))
    if not adminmode:
        data = data.filter( \
            Q(dependent_enable_public_pro=True) | \
            Q(dependent_enable_public_nc=True) | \
            Q(dependent_enable_public_ng=True))
    data = data.filter( \
        Q(dependent_asgs_pro=True) | \
        Q(dependent_asgs_nc=True) | \
        Q(dependent_asgs_ng=True))

    if asgs == 'nc':
        return data.filter( \
            Q(dependent_region_nc_ng=True) | \
            Q(dependent_region_nc=True))

    if asgs == 'ng':
        return data.filter( \
            Q(dependent_region_nc_ng=True) | \
            Q(dependent_region_ng=True))

    return data.filter( \
        Q(dependent_region_nc_ng=True) | \
        Q(dependent_region_nc=True) | \
        Q(dependent_region_ng=True))

def filter_data_by_asgs(perm, data, asgs, adminmode):
# filter_data_by_asgs(allyears, asgs)
# filter_data_by_asgs(allstorms, asgs)
# filter_data_by_asgs(alladvisories, asgs)
# filter_data_by_asgs(alltracks_base, asgs)

    # retrieve the list of all storm_years, storms, advisories or tracks (=data parameter)
    if len(asgs) > 0:

        # filter datasets by 'enable_adminmode' = True
        # (decides about the global display of a record) - all other records will not be displayed at all

        # if ADMINMODE (http.conf) is set to False (= public web server),
        # return only datasets with 'dependent_enabled_public_xx' = true

        if asgs == 'dev':
            data = data.filter(dependent_enable_adminmode_dev=True)
            if not adminmode:
                data = data.filter(dependent_enable_public_dev=True)
            return data.filter(dependent_asgs_dev=True)
        if asgs == 'pr':
            data = data.filter(dependent_enable_adminmode_pr=True)
            if not adminmode:
                data = data.filter(dependent_enable_public_pr=True)
            return data.filter(dependent_asgs_pr=True)
        if asgs == 'ri':
            data = data.filter(dependent_enable_adminmode_ri=True)
            if not adminmode:
                data = data.filter(dependent_enable_public_ri=True)
            return data.filter(dependent_asgs_ri=True)
        if asgs == 'st':
            data = data.filter(dependent_enable_adminmode_st=True)
            if not adminmode:
                data = data.filter(dependent_enable_public_st=True)
            return data.filter(dependent_asgs_st=True)

        if perm == 'pro':
            return filter_data_by_asgs_pro(perm, data, asgs, adminmode)

        if perm == 'nc_ng':
            return filter_data_by_asgs_ncng(perm, data, asgs, adminmode)

        return filter_data_by_asgs_pub(perm, data, asgs, adminmode)

    # len(asgs) == 0
    data = data.filter(dependent_enable_adminmode_pub=True)
    if not adminmode:
        data = data.filter(dependent_enable_public_pub=True)
    return data.filter(dependent_asgs_pub=True)

##############################################################################
# retrieve all adcrun_days from adcrun_info (to fill the day select box (json)
# or select the latest day as default value if no value is given on the URL)
# day is in url format (YYYYMMDD), given in UTC
def retrieve_adcrun_days(perm, day, tz, asgs, adminmode):

    alldays = []
    requested_day = None

    try:
        # retrieve the list of all adcircrun day data (alldays)
        allinfos = adcrun_info.objects.all()

        # filter datasets by 'enable_adminmode' = True
        # (decides about the global display of a record) - all other records
        # will not be displayed at all
        allinfos = allinfos.filter(enable_adminmode=True)

        # if ADMINMODE (http.conf) is set to False (= public web server),
        # return only datasets with 'enabled_public' = true
        if not adminmode:
            allinfos = allinfos.filter(enable_public=True)

        # filter for given asgs system
        allinfos = filter_allinfos_asgs(perm, allinfos, asgs)

        tz = get_pytz_timezone(tz)

        # build a list of unique days
        days = {}
        for d in allinfos:
            dt = as_timezone(d.adcrun_daytime_utc, tz)
            dt = tz.localize(datetime(dt.year, dt.month, dt.day))

            if dt in days:
                if d.has_adv:
                    days[dt] = True
            else:
                days[dt] = d.has_adv

        # build a list of adcrun_day_proxy's
        for k in sorted(days.keys()):
            alldays.append(adcrun_day_proxy(k, days[k]))

        if (len(day) > 0):
            # date format on URL is '20080830', given in local time
            dt_start = tz.localize(datetime.strptime(day, "%Y%m%d"))
            if dt_start in days:
                requested_day = adcrun_day_proxy(dt_start, days[dt_start])

        if requested_day is None and len(alldays) > 0:
            # return last day
            requested_day = alldays[-1]

    except adcrun_info.DoesNotExist:
        pass

    return (alldays, requested_day)

###########################################################################
# test for alldays
# http://[host]/cerarisk/adcircrun/day=20100902/tz=utc/asgs=ng.test
def test_retrieve_adcrun_days(request, day, tz, asgs):

    perm = 'pub'
    if request.user.is_authenticated:
        perm = request.user.userprofile.cera

    adminmode = False
    if (request.META.has_key('CERA_ADMINMODE') and request.META['CERA_ADMINMODE'] != "0"):
        adminmode = True

    if len(tz) == 0:
        tz = 'utc'

    (alldays, requested_day) = retrieve_adcrun_days(perm, day, tz, asgs, adminmode)

    return render_to_response('retrieve_adcrun_days.test', {
        'alldays': alldays, 'requested_day': requested_day, 'time_zone': tz, 'asgs': asgs
    })


########################################################################
# 'Day' tab only: retrieve all adcrun_infos  (to fill the time and modelinfo select boxes (json)
# or select the latest time/windmodel as default value if no value is given on the URL
# day in url format (YYYYMMDD), time in url format (HHMM), given in UTC

# find either the last run for no storm runs or the latest t01 run for storm runs
def retrieve_adcrun_info_last_t01(allinfos, dt = None):

    if allinfos is None:
        return None
    if len(allinfos) == 0:
        return None

    # no need to filter if there is only one run
    if len(allinfos) == 1:
        return allinfos[0]

    # return all runs even if no storm
    last_t01 = -1

    if dt is None:
        dt = allinfos[len(allinfos)-1].adcrun_daytime_utc

    # iterate over all runs to find all 't01'
    has_default_view = False
    t01_runs = []   # list of (index, default_view)
    for i, info in enumerate(allinfos):
        if info.has_adv:    # for storms
            if info.track_id.track == 't01':
                default_view = dt == info.adcrun_daytime_utc and info.default_view
                if default_view:
                    has_default_view = True
                t01_runs.append((i, default_view))

    # find last default_view or last t01
    if has_default_view:
        for index, default_view in t01_runs:
            if default_view:
                last_t01 = index    # store last default_view
    elif len(t01_runs) != 0:
        last_t01 = t01_runs[-1][0]  # get last storm

    # return only for storms
    if last_t01 != -1:
        return allinfos[last_t01]

    # iterate over all runs to find either the last one marked as default_view
    last_t01 = len(allinfos)-1

    for i, info in enumerate(allinfos):
        if dt == info.adcrun_daytime_utc and info.default_view:
            last_t01 = i

    return allinfos[last_t01]

def retrieve_adcrun_infos(perm, requested_day, tim, id, asgs, adminmode):

    allinfos = []
    alltimes = []
    requested_info = None
    try:
        # retrieve the list of all adcrun_infos for the requested day
        dt_start = requested_day.adcrun_day
        dt_end = dt_start + timedelta(days=1)
        allinfos = adcrun_info.objects                      \
            .filter(adcrun_daytime_utc__gte=dt_start)       \
            .filter(adcrun_daytime_utc__lt=dt_end)          \
            .order_by('adcrun_daytime_utc', 'id')

        # filter datasets by 'enable_adminmode' = True
        # (decides about the global display of a record) - all other records
        # will not be displayed at all
        allinfos = allinfos.filter(enable_adminmode=True)

        # if ADMINMODE (http.conf) is set to False (= public web server),
        # return only datasets with 'enabled_public' = true
        if (adminmode == False):
            allinfos = allinfos.filter(enable_public=True)

        allinfos = filter_allinfos_asgs(perm, allinfos, asgs)
        allinfos = allinfos.select_related('track_id')

        if (len(id) > 0):
            # find the specific adcrun_info via the id
            requested_info_list = allinfos.filter(id=int(id))
            if len(requested_info_list) > 0:
                requested_info = requested_info_list[0]

                # find the requested time datasets (one time can have multiple datasets)
                alltimes = allinfos.filter(adcrun_daytime_utc=requested_info.adcrun_daytime_utc)

        if not requested_info:
            # either no id or requested id not found in db
            if len(tim) > 0:
                # requested_day + time in UTC, time-aware
                t = datetime.strptime(tim, "%H%M")
                dt = requested_day.adcrun_day + timedelta(seconds=t.hour*3600+t.minute*60)

                # find the requested time datasets (one time can have multiple datasets)
                alltimes = allinfos.filter(adcrun_daytime_utc=dt)

                if len(alltimes) > 0:
                    # retrieve last for the given day/time
                    requested_info = retrieve_adcrun_info_last_t01(alltimes, dt)
#                   allinfos = alltimes
                elif len(allinfos):
                    # should not happen, requested time not found in db
                    requested_info = retrieve_adcrun_info_last_t01(allinfos, dt)
#                    allinfos = []
                    alltimes = []

            elif len(allinfos) > 0:
                # no time on URL, retrieve last for the given day
                requested_info = retrieve_adcrun_info_last_t01(allinfos)

        if len(allinfos) > 0:
            alltimes = sorted(
                dict(map(lambda t: (t.adcrun_daytime_utc, t), allinfos)).values(),
                key=adcrun_info.get_adcrun_time)

    except adcrun_info.DoesNotExist:
        pass

    return (allinfos, requested_info, alltimes)


########################################################################
# test for allinfos
# http://[host]/cerarisk/adcircrun/day=20110825/time=0600/id=1/tz=utc/asgs=ng.test
def test_retrieve_adcrun_infos(request, day, time, id, tz, asgs):

    perm = 'pub'
    if request.user.is_authenticated:
        perm = request.user.userprofile.cera

    adminmode = False
    if (request.META.has_key('CERA_ADMINMODE') and request.META['CERA_ADMINMODE'] != "0"):
        adminmode = True

    (alldays, requested_day) = retrieve_adcrun_days(perm, day, tz, asgs, adminmode)
    (allinfos, requested_info, alltimes) = retrieve_adcrun_infos(perm, requested_day, time, id, asgs, adminmode)

    return render_to_response('retrieve_adcrun_infos.test', {
        'allinfos': allinfos, 'requested_info': requested_info, 'alltimes': alltimes, 'time_zone': tz
    })

################################################################################################
# select all storm years filtered by asgs
def retrieve_adcrun_years(perm, yr, asgs, adminmode):

    allyears = []
    requested_year = None

    try:
        allyears = storm_year.objects.all()

        # retrieve the list of all storm_years
        allyears = filter_data_by_asgs(perm, allyears, asgs, adminmode)
        allyears = allyears.order_by('year')

        # if yr is given, select the requested year from allyears
        if len(yr) > 0:
            requested_years = allyears.filter(year=yr)
            if len(requested_years) > 0:
                requested_year = requested_years[0]
            else:
                requested_year = allyears[len(allyears)-1]

        # no yr given, select last yr from allyears
        elif len(allyears) > 0:
            requested_year = allyears[len(allyears)-1]

    except storm_year.DoesNotExist:
        pass

    return (allyears, requested_year)


########################################################################
# test for allyears
# http://[host]/cerarisk/adcircrun/year=/asgs=ng.test
def test_retrieve_adcrun_years(request, year, asgs):

    perm = 'pub'
    if request.user.is_authenticated:
        perm = request.user.userprofile.cera

    adminmode = False
    if (request.META.has_key('CERA_ADMINMODE') and request.META['CERA_ADMINMODE'] != "0"):
        adminmode = True

    (allyears, requested_year) = retrieve_adcrun_years(perm, year, asgs, adminmode)

    return render_to_response('retrieve_adcrun_years.test', {
        'allyears': allyears, 'requested_year': requested_year
    })

################################################################################################
# select all storms (independent from the requested storm) to fill the year/storm select box
# the dependency of the years/storms will be set in the json template
def retrieve_adcrun_storms(perm, requested_year, stormnr, asgs, adminmode):

    if requested_year is None:
        return ([], None)

    allstorms = []
    requested_storm = None

    try:
        # retrieve the list of all adcircrun day data (alldays)
        allstorms = storm.objects.all()
        allstorms = filter_data_by_asgs(perm, allstorms, asgs, adminmode)
        allstorms = allstorms \
            .order_by('-year', 'stormname') \
            .select_related('year')

        # if stormnr is given, select the requested storm for the requested year from allstorms
        if len(stormnr) > 0:
            requested_storms = allstorms.filter(year=requested_year.id).filter(storm_number=stormnr)
            if len(requested_storms) > 0:
                requested_storm = requested_storms[0]

        # no stormnr given, select last existing storm
        elif len(allstorms) > 0:
            requested_storms = allstorms.filter(year=requested_year.id)
            if len(requested_storms) > 0:
                requested_storm = requested_storms[len(requested_storms)-1]

    except storm.DoesNotExist:
        pass

    return (allstorms, requested_storm)

###########################################################################
# test for allstorms
# http://[host]/cerarisk/adcircrun/year=2010/stormnr=09/asgs=ng.test
def test_retrieve_allstorms(request, year, stormnr, asgs):

    perm = 'pub'
    if request.user.is_authenticated:
        perm = request.user.userprofile.cera

    adminmode = False
    if (request.META.has_key('CERA_ADMINMODE') and request.META['CERA_ADMINMODE'] != "0"):
        adminmode = True

    # filter for given asgs system and
    # get all relevant years and the requested year (given on URL or last year in the list)
    (allyears, requested_year) = retrieve_adcrun_years(perm, year, asgs, adminmode)

    (allstorms, requested_storm) = retrieve_adcrun_storms(perm, requested_year, stormnr, asgs, adminmode)

    return render_to_response('retrieve_allstorms.test', {
        'allyears': allyears, 'requested_year': requested_year,
        'allstorms': allstorms, 'requested_storm': requested_storm
    })

################################################################################################
# select all advisories for the requested storm
def retrieve_adcrun_advisories(perm, requested_storm, adv, asgs, adminmode):

    if requested_storm is None:
        return ([], None)

    alladvisories = []
    requested_advisory = None

    try:
        alladvisories = advisory.objects.all()
        alladvisories = filter_data_by_asgs(perm, alladvisories, asgs, adminmode)
        alladvisories = alladvisories.filter(storm=requested_storm.id) \
            .order_by('adv_time_utc') \
            .order_by('advisory')

        # if adv is given, select the requested advisory from alladvisories
        if len(alladvisories) > 0:
            if len(adv) > 0:
                requested_advisories = alladvisories.filter(advisory=adv)
                if len(requested_advisories) > 0:
                    requested_advisory = requested_advisories[0]
                else:
                    requested_advisory = alladvisories[len(alladvisories)-1]

            # no adv given, select last existing advisory
            else: #if len(alladvisories) > 0:
                requested_advisory = alladvisories[len(alladvisories)-1]

    except advisory.DoesNotExist:
        pass

    return (alladvisories, requested_advisory)

################################################################################################
# select all tracks (for all advisories of the requested storm) to fill the advisory/track select box
# the dependency of the advisories/tracks will be set in the json template
def retrieve_adcrun_tracks(perm, alladvisories, requested_advisory, tracknr, trackpercent, asgs, adminmode):

    if alladvisories is None:
        return ([], None, None)
    if requested_advisory is None:
        return ([], None, None)

    tracks = []
    requested_track = None

    alltracks = []
    try:
        # retrieve the list of all track records belonging to any advisory in 'alladvisories' (for the requested year and storm)
        alltracks_base = track.objects.all()
        alltracks_base = filter_data_by_asgs(perm, alltracks_base, asgs, adminmode)

        # filter all tracks which belong to any given advisory in alladvisories
        if len(alladvisories) > 0:
            from django.db.models import Q
            import operator

            query = []
            for a in alladvisories:
                query.append(Q(advisory=a.id))

            alltracks = alltracks_base \
                .filter(reduce(operator.or_, query)) \
                .order_by('-advisory', 'track', 'mod_percent') \
                .select_related('advisory')

        else:
            alltracks = alltracks_base \
                .order_by('-advisory', 'track', 'mod_percent') \
                .select_related('advisory')

        # check whether the retrieved tracks belong to the requested_advisory
        tracks_requested_advisory = alltracks.filter(advisory=requested_advisory.id)

        if len(tracks_requested_advisory) > 0:
        # if tracknr is given, select the requested track from tracks_requested_advisory
            if len(tracknr) > 0:
                requested_tracks = tracks_requested_advisory.filter(track=tracknr)
                if len(trackpercent) > 0:
                    requested_tracks = requested_tracks.filter(mod_percent=trackpercent)

                if len(requested_tracks) > 0:
                    requested_track = requested_tracks[0]

            # no tracknr given, select last existing track from tracks_requested_advisory
            elif len(tracks_requested_advisory) > 0:
                if len(trackpercent) > 0:
                    requested_tracks = tracks_requested_advisory.filter(mod_percent=trackpercent)

                requested_track = tracks_requested_advisory[0]   # select t01 as default


    except track.DoesNotExist:
        pass

    return (alltracks, requested_track, tracks_requested_advisory)

###########################################################################
# test for alltracks
# http://[host]/cerarisk/adcircrun/year=/stormnr=/adv=/tracknr=/tz=/asgs=ng.test
def test_retrieve_alltracks(request, year, stormnr, adv, tracknr, tz, asgs):

    perm = 'pub'
    if request.user.is_authenticated:
        perm = request.user.userprofile.cera

    adminmode = False

    if (request.META.has_key('CERA_ADMINMODE') and request.META['CERA_ADMINMODE'] != "0"):
        adminmode = True

    # get all years and the requested year (given on URL or last year in the list)
    (allyears, requested_year) = retrieve_adcrun_years(perm, year, asgs, adminmode)

    # get all storms and the requested storm (given on URL or last storm in the list)
    allstorms = []
    requested_storm = None
    if requested_year is not None:
        (allstorms, requested_storm) = retrieve_adcrun_storms(perm, requested_year, stormnr, asgs, adminmode)

    # get all advisories and the requested advisory (given on URL or last advisory in the list)
    alladvisories = []
    requested_advisory = None
    if requested_storm is not None:
        (alladvisories, requested_advisory) = retrieve_adcrun_advisories(perm, requested_storm, adv, asgs, adminmode)

    # get all tracks and the requested track (given on URL or last track in the list)
    alltracks = []
    requested_track = None
    tracks = None
    if requested_advisory is not None:
        (alltracks, requested_track, tracks) = retrieve_adcrun_tracks(perm, alladvisories, requested_advisory, tracknr, '', asgs, adminmode)

    return render_to_response('retrieve_alltracks.test', {
        'alladvisories': alladvisories, 'requested_advisory': requested_advisory,
        'alltracks': alltracks, 'requested_track': requested_track,
        'tracks': tracks
    })

###########################################################################
def getadcircrun_id(perm, day, time, id, tz, asgs, adminmode):

    # retrieve data for adcrun_days
    alldays = []
    requested_day = None
    (alldays, requested_day) = retrieve_adcrun_days(perm, day, tz, asgs, adminmode)

    # retrieve data for adcircrun_info
    allinfos = []
    requested_info = None
    alltimes = []
    if alldays and len(alldays) > 0:
        (allinfos, requested_info, alltimes) = retrieve_adcrun_infos(perm, requested_day, time, id, asgs, adminmode)

        # filter out all unrelated adcrun_info records if time is given
        if allinfos is not None and requested_info is not None:
            allinfos = allinfos.filter(adcrun_daytime_utc=requested_info.adcrun_daytime_utc)

    return (alldays, requested_day, allinfos, requested_info, alltimes)

###########################################################################
def getadcircrun_storminfo(perm, yr, stormnr, adv, tracknr, trackpercent, asgs, adminmode):

    # get all years and the requested year (given on URL or last year in the list)
    (allyears, requested_year) = retrieve_adcrun_years(perm, yr, asgs, adminmode)

    # get all storms and the requested storm (given on URL or last storm in the list)
    allstorms = []
    requested_storm = None
    if requested_year is not None:
        (allstorms, requested_storm) = retrieve_adcrun_storms(perm, requested_year, stormnr, asgs, adminmode)

    # get all advisories and the requested advisory (given on URL or last advisory in the list)
    alladvisories = []
    requested_advisory = None
    if requested_storm is not None:
        (alladvisories, requested_advisory) = retrieve_adcrun_advisories(perm, requested_storm, adv, asgs, adminmode)

    # get all tracks and the requested track (given on URL or last track in the list)
    alltracks = []
    requested_track = None
    if requested_advisory is not None:
        (alltracks, requested_track, dummy) = retrieve_adcrun_tracks(perm, alladvisories, requested_advisory, tracknr, trackpercent, asgs, adminmode)

    return (allyears, requested_year, allstorms, requested_storm, alladvisories, requested_advisory, alltracks, requested_track)

###########################################################################
def get_infos_from_track(perm, requested_track_id, asgs, adminmode):

    allinfos = adcrun_info.objects \
        .filter(track_id=requested_track_id) \
        .select_related('track_id')

    allinfos = filter_allinfos_asgs(perm, allinfos, asgs)

    # filter datasets by 'enable_adminmode' = True
    # (decides about the global display of a record) - all other records
    # will not be displayed at all
    allinfos = allinfos.filter(enable_adminmode=True)

    # if ADMINMODE (http.conf) is set to False (= public web server),
    # return only datasets with 'enabled_public' = true
    if (adminmode == False):
        allinfos = allinfos.filter(enable_public=True)

    return allinfos

###########################################################################
def getadcircrun_subtracks(perm, requested_info, asgs, adminmode):

    subtracks = subtrack.objects \
        .filter(adcrunid=requested_info.id) \
        .select_related('adcrunid', 'trackid__advisory__storm')

    dependent_modelruns = []
    for s in subtracks:
        allinfos = get_infos_from_track(perm, s.trackid.id, asgs, adminmode)
        allinfos = allinfos.filter(windmodel=requested_info.windmodel)

        allinfos_samegrid = allinfos.filter(grid=requested_info.grid)

        dependent_modelrun = {
            "text": s.trackid.advisory.storm.stormname,
            "value": s.trackid.advisory.storm.storm_number,
            "trackid": s.trackid.id
        }
        # if a subtrack with the same grid exists, show this run; otherwise any other run with the same wind model
        if len(allinfos_samegrid) > 0:
            dependent_modelrun.update({ "com": str(allinfos_samegrid[0].id) })
        elif len(allinfos) > 0:
            dependent_modelrun.update({ "com": str(allinfos[0].id) })

        dependent_modelruns.append(dependent_modelrun)

    return dependent_modelruns

###########################################################################
# if CERA opens the first time, the id is not known - provide all information to get it
# cera.json: http://[host]/cerarisk/adcircrun/day=/time=/id=/yr=2010/stormnr=07/adv=31/tracknr=t01_0/tz=utc/asgs=all/dev=0.json
def getadcircrun_redirect(request, day, time, id, yr, stormnr, adv, tracknr, tz, asgs, dev):

    perm = 'pub'
    if request.user.is_authenticated:
        perm = request.user.userprofile.cera

    url = '/cerarisk/adcircrun/day=%s/time=%s/id=%s/yr=%s/stormnr=%s/adv=%s/tracknr=%s/tz=%s/asgs=%s/dev=%s/perm=%s.json'
    url = url % (day, time, id, yr, stormnr, adv, tracknr, tz, asgs, dev, perm)

    try:
        from django.conf import settings
        # twister goes to local django, all other to ncrenci-1
        if settings.CERA_ENV.has_key('REDIRECT_DBHOST'):
            server = settings.CERA_ENV['REDIRECT_DBHOST']
        else:
            server = 'nccera-1.renci.org'
        conn = httplib.HTTPConnection(server)
        conn.request('GET', url)
        r = conn.getresponse()

        resp = HttpResponse(r.read(), status=r.status)
        for (key, value) in r.getheaders():
            from wsgiref.util import is_hop_by_hop
            if not is_hop_by_hop(key):
                resp[key] = value

    except Exception, e:
        resp = HttpResponse(str(e), status=500)

    return resp

def getadcircrun(request, day, time, id, yr, stormnr, adv, tracknr, tz, asgs, dev, perm='pub'):

    if not perm in ['pub', 'nc_ng', 'pro']:
      raise ValidationError(
        'CERA site permisission \'%(perm)s\' not supported.',
        params = { 'perm' : perm }
      )

    if perm == 'pub' and request.user.is_authenticated:
        perm = request.user.userprofile.cera

    adminmode = False
    if (request.META.has_key('CERA_ADMINMODE') and request.META['CERA_ADMINMODE'] != "0"):
        adminmode = True

    alldays = None
    requested_info = None
    requested_track = None
    selected_tracks = None
    selected_track = None

    # e.g. t05_+50
    tracknr_storm = tracknr
    trackpercent_storm = ''
    if len(tracknr) > 0:
        t = tracknr.split('_')
        tracknr_storm = t[0]
        if len(t) > 1:
            trackpercent_storm = t[1]

    if len(id) == 0 and len(yr) == 0 and len(stormnr) == 0 and len(adv) == 0 and len(tracknr) == 0:
        # if no storm related parameters are given, assume user has
        # performed a selection from the 'day' tab or opens CERA for the first time
        # http://[host]/cerarisk/adcircrun/day=20110825/time=0600/id=1/yr=/stormnr=/adv=/tracknr=/tz=utc/asgs=nc/dev=0.json

        # get all days to fill the day select box (alldays, requested_day)
        # get all times for selected day to fill the time select box (alltimes)
        # get all adcrun_infos to fill the modelinfo select box, grid etc. (allinfos, requested_info)
        (alldays, requested_day, allinfos, requested_info, alltimes) = getadcircrun_id(perm, day, time, id, tz, asgs, adminmode)

        # if the selected run is a storm, preselect all storm related fields

        yr_storm = yr
        stormnr_storm = stormnr
        adv_storm = adv
        # get the storm info for the requested run and dispplay it in the storm select boxes
        if requested_info is not None and requested_info.has_adv:
            selected_tracks = track.objects \
                .filter(id=requested_info.track_id_id) \
                .select_related('advisory__storm__year')

            if len(selected_tracks) > 0:
                selected_track = selected_tracks[0]
                yr_storm = str(selected_track.advisory.storm.year.year)
                stormnr_storm = str(selected_track.advisory.storm.storm_number)
                adv_storm = str(selected_track.advisory.advisory)
                tracknr_storm = selected_track.track
                trackpercent_storm = selected_track.mod_percent

        # get all storminfo to fill the year,storm,advisory,track select boxes
        (allyears, requested_year, allstorms, requested_storm, alladvisories, requested_advisory, alltracks, requested_track) = \
            getadcircrun_storminfo(perm, yr_storm, stormnr_storm, adv_storm, tracknr_storm, trackpercent_storm, asgs, adminmode)

        if selected_tracks is not None:
            if len(selected_tracks) > 0:
                 requested_track = selected_track

        # if storm has hindcast make sure the hindcast is preselected
        if len(adv) == 0 and requested_info is not None and requested_info.has_adv and \
            requested_storm is not None and requested_storm.has_hindcast and len(day) == 0:

            # retrieve the hindcast advisory
            requested_advisories = alladvisories.filter(advisory='999')
            if len(requested_advisories) > 0 and requested_advisory != requested_advisories[0]:
                requested_advisory = requested_advisories[0]

                # get all tracks and the last track in the list
                alltracks = []
                requested_track = None
                if requested_advisory is not None:
                    (alltracks, requested_track, dummy) = retrieve_adcrun_tracks(perm, alladvisories, requested_advisory, '', '', asgs, adminmode)

                alldays = None                  # redo the query
                requested_info = None

#        if requested_info is not None and requested_info.has_adv and requested_track is not None:
#            allinfos = get_infos_from_track(perm, requested_track.id, asgs, adminmode)
#            if len(allinfos) > 0:
#                requested_info = allinfos[0]
#                alldays = None                  # redo the query

    else:
        # if at least one storm related parameter is given, assume user has
        # performed a selection from the 'storm' tab
        # http://[host]/cerarisk/adcircrun/day=/time=/id=/yr=2011/stormnr=09/adv=20/tracknr=t01/tz=utc/asgs=all.json

        if len(id) > 0:
            allinfos = adcrun_info.objects.filter(id=id)
            allinfos = filter_allinfos_asgs(perm, allinfos, asgs)
            if len(allinfos) > 0:
                requested_info = allinfos[0]
                selected_tracks = track.objects \
                    .filter(id=requested_info.track_id_id) \
                    .select_related('advisory__storm__year')

                if len(selected_tracks) > 0:
                    requested_track = selected_tracks[0]
                    if len(yr) == 0:
                        yr = str(requested_track.advisory.storm.year.year)
                    if len(stormnr) == 0:
                        stormnr = str(requested_track.advisory.storm.storm_number)
                    if len(adv) == 0:
                        adv = str(requested_track.advisory.advisory)
                    if len(tracknr) == 0:
                        tracknr_storm = requested_track.track
                        trackpercent_storm = requested_track.mod_percent
            else:
                # insufficient rights to view requested run or non-existing run
                yr = ''
                stormnr = ''
                adv = ''
                tracknr = ''

        # get all years and for each year all storms to fill the year/storm select box:
        #   (allyears, requested_year, allstorms, requested_storm)
        # get all advisories and for each advisory all tracks to fill the advisory/track select box:
        #   (alladvisories, requested_advisory, alltracks, requested_track)
        (allyears, requested_year, allstorms, requested_storm, alladvisories, requested_advisory, alltracks, requested_track_dummy) = \
            getadcircrun_storminfo(perm, yr, stormnr, adv, tracknr_storm, trackpercent_storm, asgs, adminmode)
        if requested_track is None:
            requested_track = requested_track_dummy

    if requested_info is None:
        if requested_track is not None:
            allinfos = get_infos_from_track(perm, requested_track.id, asgs, adminmode)

        if allinfos is not None:
            if len(allinfos) > 0:
                requested_info = retrieve_adcrun_info_last_t01(allinfos)

    if requested_info is not None:
        # if requested_info is not a storm, leave selection for storm empty
        if not requested_info.has_adv:
            requested_year = None
            requested_storm = None
            requested_advisory = None
            requested_track = None

        dt = as_timezone(requested_info.adcrun_daytime_utc, get_pytz_timezone(tz))
        day = dt.strftime("%Y%m%d")
        time = dt.strftime("%H%M")
        id = str(requested_info.id)

    if alldays is None:
        (alldays, requested_day, dummy1, dummy2, alltimes) = getadcircrun_id(perm, day, time, id, tz, asgs, adminmode)
        if True: #allinfos is None:
            allinfos = dummy1
        if True: #requested_info is None:
            requested_info = dummy2

    # build list of displayed layers
    layers = []
    first_timestep = None
    if requested_info is not None:

        layernames = [
            'elev', 'inun', 'hsign', 'tps', 'wvel',
            'maxelev', 'maxinun', 'maxhsign', 'maxtps', 'maxwvel',
            'maxelev_auto', 'maxinun_auto', 'maxhsign_auto', 'maxtps_auto', 'maxwvel_auto',
            'wvelf', 'hydro', 'prec', 'precimg', 'diffmaxwvelhist',
            'track_invest', 'track_sub',
            'maxelevshp', 'maxinunshp', 'maxhsignshp', 'maxtpsshp', 'maxwvelshp', 'maxwvel10shp',
            'elevshp', 'inunshp', 'hsignshp', 'tpsshp', 'wvelshp', 'wvel10shp',
        ]

        from django.db.models import Q
        import operator

        query = []
        for l in layernames:
            query.append(Q(layername=l))

        layer_infos = layerinfo.objects \
            .filter(adcrun_info=requested_info.id) \
            .filter(reduce(operator.or_, query)) \
            .filter(show_layer=True)

        for info in layer_infos:
            if info.layername == 'wvel10shp':
                layers.append('wvelshp')
            elif info.layername == 'maxwvel10shp':
                layers.append('maxwvelshp')
            else:
                layers.append(info.layername)

        if (requested_info.has_adv): layers.append("trackline")

        first_timestep = (requested_info.adcrun_daytime_utc + timedelta(seconds=3600)).strftime("%Y%m%dT%H00")

    # find subtracks
    subtracks = None
    if requested_info is not None:
        subtracks = getadcircrun_subtracks(perm, requested_info, asgs, adminmode)

    # filter allinfos for day tab (model info select box = 'comment_day')
    def is_day_info(info):
        if not info.has_adv:
            return True        # include all no-storms
        if info.id == requested_info.id:
            return True        # selected run from 'storm tab' is always shown even if track variation (!=t01)
        if info.grid == requested_info.grid and info.windmodel == requested_info.windmodel and info.asgs_instance == requested_info.asgs_instance:
            return False       # not if same grid/windmodel as selected run unless it is a different asgs_instance

        return info.track_id.track == 't01'   # all remaining tracks only if 't01'

    # order the modelinfo list ascending
    allinfos_day = filter(is_day_info, allinfos.order_by('windmodel','grid'))

    allinfos_day_has_adv = False
    for info in allinfos:
        if info.has_adv:
            allinfos_day_has_adv = True
            break

    # filter allinfos for storm tab (model info select box = 'comment_storm')
    def is_storm_info(info):
        if not info.has_adv:
            return False       # only storms
        if not requested_track:
            return False       # only if a track has been selected
        return info.track_id.id == requested_track.id   # and only from selected track

    allinfos_storm = filter(is_storm_info, allinfos.order_by('windmodel','grid'))

    # return...(html_templates/cera.json),{arbitrary name to be used in html template : variable name})
    return render_to_response('cera.json', {
        'alldays': alldays, 'requested_day': requested_day,
        'alltimes': alltimes, 'requested_info': requested_info,
#        'allinfos': allinfos,
        'layers': layers,
        'allinfos_day': allinfos_day, 'allinfos_day_has_adv' : allinfos_day_has_adv,
        'allinfos_storm': allinfos_storm,
        'allyears': allyears, 'requested_year': requested_year,
        'allstorms': allstorms, 'requested_storm': requested_storm,
        'alladvisories': alladvisories, 'requested_advisory': requested_advisory,
        'alltracks': alltracks, 'requested_track': requested_track,
        'time_zone': tz, 'asgs': asgs,
        'yr': yr, 'stormnr': stormnr, 'adv': adv, 'day': day, 'time': time, 'id': id,
        'first_timestep': first_timestep,
        'dev_site': dev,
        'subtracks': subtracks,
        'perm' : perm
    })

#################################################################################################
# header: [host]/cerarisk/adcircrun/id=1/tz=utc/asgs=all.hd
# datetimes given in UTC
# asgs is not needed here, but is on the data_url in the html which is used for both the json and header files (json needs the asgs)
def getheader(request, id, tz, asgs):

    adminmode = False
    if (request.META.has_key('CERA_ADMINMODE') and request.META['CERA_ADMINMODE'] != "0"):
        adminmode = True

    requested_info = None

    # daytime from requested info is needed to fill the header
    if len(id) > 0:
        allinfos = adcrun_info.objects.filter(id=id)
        if len(allinfos) > 0:
            requested_info = allinfos[0]

    if requested_info is None:
        from django.http import Http404
        raise Http404

    # return...(templates/header.html),{arbitrary name to be used in html template : variable name})
    return render_to_response('header.html',
        { 'requested_info': requested_info, 'time_zone': tz })

#################################################################################################
# header storm/daily: http://[host]/cerarisk/adcircrun/id=3695/tz=cdt/asgs=ng.hdstorm
# asgs is not needed here, but is on the data_url in the html which is used for both the json and header files (json needs the asgs)
def getheaderstorm(request, id, tz, asgs):

    adminmode = False
    if (request.META.has_key('CERA_ADMINMODE') and request.META['CERA_ADMINMODE'] != "0"):
        adminmode = True

    requested_info = None
    if len(id) > 0:
        allinfos = adcrun_info.objects.filter(id=id)
        if len(allinfos) > 0:
            requested_info = allinfos[0]

    if requested_info is None:
        from django.http import Http404
        raise Http404

    requested_track = None

    if len(id) > 0:
        allinfos = adcrun_info.objects.filter(id=id)
        if len(allinfos) > 0:
            requested_info = allinfos[0]
            selected_tracks = track.objects \
                .filter(id=requested_info.track_id_id)

            if len(selected_tracks) > 0:
                selected_tracks.select_related('advisory__storm__year')
                requested_track = selected_tracks[0]

    if requested_track is None:
#        from django.http import Http404
#        raise Http404
        # daily
        return render_to_response('header_daily.html',
            { 'requested_info': requested_info, 'time_zone': tz })
    else:
        return render_to_response('header_storm.html',
            { 'requested_info': requested_info, 'advisory': requested_track.advisory, 'track': requested_track, 'time_zone': tz })

#################################################################################################
# header remark: http://[host]/cerarisk/adcircrun/id=3695/asgs=ng.hdremark
# asgs is not needed here, but is on the data_url in the html which is used for both the json and header files (json needs the asgs)
def getheader_remark(request, id, asgs):

    adminmode = False
    if (request.META.has_key('CERA_ADMINMODE') and request.META['CERA_ADMINMODE'] != "0"):
        adminmode = True

    requested_info = None
    # get remark from requested info
    if len(id) > 0:
        allinfos = adcrun_info.objects.filter(id=id)
        if len(allinfos) > 0:
            requested_info = allinfos[0]

    if requested_info is None:
        from django.http import Http404
        raise Http404

    requested_remark = None
    if requested_info is not None:
        requested_remark = requested_info.remark

    if requested_remark is None or len(requested_remark) == 0:
        from django.http import Http404
        raise Http404

    return render_to_response('header_remark.html',
        { 'requested_remark': requested_remark })

################################################################################################
# legend: http://[host]/cerarisk/adcircrun/id=[id]/tz=edt/layer=maxelev/dev=0/unit=ft.html

def retrieve_color_values(id, requested_info, layername):

    values = None
    try:
        import json
    except Exception, e:
        import simplejson as json   # Python V2.5 has no json module

    # load adcirc.json
    if 1: #try:
        daytime = requested_info.adcrun_daytime_utc
        targetpath = '/cera_wms_data/%s/%02d/%02d/%02d/%s/%s/adcirc.json' % (
            daytime.year, daytime.month, daytime.day, daytime.hour, id, layername)

        conn = httplib.HTTPConnection(requested_info.get_wmsserver_display())
        conn.request('GET', targetpath)
        r = conn.getresponse()
        if (r.status == 200):
            d = json.loads(r.read())
            if d.has_key('values'):
                values = d['values']

    #except Exception, e:
    #    pass

    return values

#def retrieve_bathy_color_values(requested_info):

#    values = None
#    try:
#	import json
#    except Exception, e:
#        import simplejson as json   # Python V2.5 has no json module

    # load adcirc.json
#    if 1: #try:
#        targetpath = '/cera_wms_data/adcirc_features/bathy/%s/adcirc.json' % (
#            requested_info.get_grid_display())

#        conn = httplib.HTTPConnection(requested_info.get_wmsserver_display())
#        conn.request('GET', targetpath)
#        r = conn.getresponse()
#        if (r.status == 200):
#            d = json.loads(r.read())
#            if d.has_key('values'):
#                values = d['values']

    #except Exception, e:
    #    pass

#    return values


def getlegend_redirect(request, id, tz, layer, dev, unit):

    url = '/cera_data/adcircrun/id=%s/tz=%s/layer=%s/dev=%s/unit=%s.html' % (id, tz, layer, dev, unit)

    try:
        from django.conf import settings
        if settings.CERA_ENV.has_key('REDIRECT_DBHOST'):
            server = settings.CERA_ENV['REDIRECT_DBHOST']
        else:
            server = 'nccera-1.renci.org'
        conn = httplib.HTTPConnection(server)
        conn.request('GET', url)
        r = conn.getresponse()

        resp = HttpResponse(r.read(), status=r.status)
        for (key, value) in r.getheaders():
            from wsgiref.util import is_hop_by_hop
            if not is_hop_by_hop(key):
                resp[key] = value

    except Exception, e:
        resp = HttpResponse(str(e), status=500)

    return resp

def getlegend(request, id, tz, layer, dev, unit):

#    adminmode = False
#    if (request.META.has_key('CERA_ADMINMODE') and request.META['CERA_ADMINMODE'] != "0"):
#        adminmode = True

    maintrack = False

    requested_info_list = adcrun_info.objects.all().filter(id=int(id))
    if len(requested_info_list) > 0:
        requested_info = requested_info_list[0]

    # 1.+2. autocolor values in adcirc.json: (2) coeff for unit conversion left side of legend img (e.g. from m to ft),
    #                                        (3) coeff for unit conversion right side of legend img (e.g. from m/s to kmh)
    layernames = {
        'maxelev': (None, None),
        'maxinun': (None, None),
        'maxhsign': (None, None),
        'maxtps': (None, None),
        'maxwvel': (None, None),
        'maxelev_auto': (3.28083, None),
        'maxinun_auto': (3.28083, None),
        'maxhsign_auto': (3.28083, None),
        'maxtps_auto': (None, None),
        'maxwvel_auto': (2.236936, 3.6),
        'diffmaxwvelhist': (None, None),
        'elev': (None, None),
        'inun': (None, None),
        'hsign': (None, None),
        'tps': (None, None),
        'wvel': (None, None),
        'maxelevshp': (None, None),
        'maxinunshp': (None, None),
        'maxhsignshp': (None, None),
        'maxtpsshp': (None, None),
        'maxwvelshp': (None, None),
        'maxwvel10shp': (None, None),
        'elevshp': (None, None),
        'inunshp': (None, None),
        'hsignshp': (None, None),
        'tpsshp': (None, None),
        'wvelshp': (None, None),
        'wvel10shp': (None, None),
        'wvelf': (None, None),
        'hydro': (None, None),
        'hydroval': (None, None),
        'prec': (None, None),
        'precimg': (None, None),
        'track_sub': (None, None),
        'track_invest': (None, None)
#       'bathy': (3.28083, None)
    }

    for l in layernames.keys():
        if l == 'wvel10shp':
            l = 'wvelshp'
        elif l == 'maxwvel10shp':
            l = 'maxwvelshp'

        exec "show_%s = False" % l
        # for autocolors: left side of legend img values
        if layernames[l][0] is not None:
            exec "%s_left_color_values = None" % l
        # for autocolors: right side of legend img values
        exec "%s_color_values = None" % l

    wind10 = False
    if requested_info is not None:

        from django.db.models import Q
        import operator

        query = []

        for l in layernames.keys():
            query.append(Q(layername=l))

        layer_infos = layerinfo.objects \
            .filter(adcrun_info=requested_info.id) \
            .filter(reduce(operator.or_, query)) \
            .filter(show_layer=True)

        for info in layer_infos:
            if info.layername == 'wvel10shp':
                layername = 'wvelshp'
                wind10 = True
            elif info.layername == 'maxwvel10shp':
                layername = 'maxwvelshp'
                wind10 = True
            else:
                layername = info.layername

            exec "show_%s = %s" % (layername, info.show_layer)
            if layer == layername and layername.find('_auto') != -1:
                values = retrieve_color_values(id, requested_info, layername)
                if values is not None:
                    if layernames[layername][0] is not None:
                        left_values = [ "%0.2f" % (float(x) * layernames[layername][0]) for x in values ]
                        exec "%s_left_color_values = %s" % (layername, left_values)

                    if layernames[layername][1] is not None:
                        right_values = [ "%0.2f" % (float(x) * layernames[layername][1]) for x in values ]
                    else:
                        right_values = values

                    exec "%s_color_values = %s" % (layername, right_values)

#            if layernames[info.layername][0]:
#                exec "%s_start = info.layer_output_start" % info.layername
#                exec "%s_end = info.layer_output_end" % info.layername


        # show in legend: jump to timesteps from track
        timesteps = False
        if show_elev or show_inun or show_hsign or show_tps or show_wvel or show_elevshp or show_inunshp or show_hsignshp or show_tpsshp or show_wvelshp:
            timesteps = True

        # show in legend: main track
        requested_tracks = track.objects.filter(id = requested_info.track_id_id)
        if len(requested_tracks) > 0:
            t = requested_tracks[0].track
            maintrack = (t == "t04" or t == "t05" or t == "t14" or t == "t15")

    # find associated asgs systems via 'requested_info.id' in 'asgs_system'
#    asgs_list = asgs_system.objects.filter(adcrun_info=requested_info.id).order_by('asgs')

    if dev == '3': # CERA stations website
        template = 'legend_stations.html'
    elif dev == '4': # CERA planning website
        template = 'legend_planning.html'
    else:
        if requested_info.program_version <= 6:  #tif
            template = 'legend_oldversions.html'
        else:
            template = 'legend.html'             #shp

    return render_to_response(template,
        {
          'requested_info': requested_info,
          'show_maxelev': show_maxelev,
          'show_maxinun': show_maxinun,
          'show_maxhsign': show_maxhsign,
          'show_maxtps': show_maxtps,
          'show_maxwvel': show_maxwvel,
          'show_maxelev_auto': show_maxelev_auto, 'maxelev_auto_color_values': maxelev_auto_color_values, 'maxelev_auto_left_color_values': maxelev_auto_left_color_values,
          'show_maxinun_auto': show_maxinun_auto, 'maxinun_auto_color_values': maxinun_auto_color_values, 'maxinun_auto_left_color_values': maxinun_auto_left_color_values,
          'show_maxhsign_auto': show_maxhsign_auto, 'maxhsign_auto_color_values': maxhsign_auto_color_values, 'maxhsign_auto_left_color_values': maxhsign_auto_left_color_values,
          'show_maxtps_auto': show_maxtps_auto, 'maxtps_auto_color_values': maxtps_auto_color_values,
          'show_maxwvel_auto': show_maxwvel_auto, 'maxwvel_auto_color_values': maxwvel_auto_color_values, 'maxwvel_auto_left_color_values': maxwvel_auto_left_color_values,

          'show_diffmaxwvelhist': show_diffmaxwvelhist,

          'show_elev': show_elev, 'show_inun': show_inun, 'show_hsign': show_hsign, 'show_tps': show_tps, 'show_wvel': show_wvel,
          'show_wvelf': show_wvelf, 'show_hydro': show_hydro, 'show_hydroval': show_hydroval, 'show_prec': show_prec, 'show_precimg': show_precimg,

          'show_maxelevshp': show_maxelevshp,
          'show_maxinunshp': show_maxinunshp,
          'show_maxhsignshp': show_maxhsignshp,
          'show_maxtpsshp': show_maxtpsshp,
          'show_maxwvelshp': show_maxwvelshp,
          'show_elevshp': show_elevshp,
          'show_inunshp': show_inunshp,
          'show_hsignshp': show_hsignshp,
          'show_tpsshp': show_tpsshp,
          'show_wvelshp': show_wvelshp,

          'show_trackinvest': show_track_invest, 'show_tracksub': show_track_sub,

#          'bathy_color_values': bathy_color_values, 'bathy_left_color_values': bathy_left_color_values,

          # show in legend: jump to timesteps from track
          'timesteps': timesteps,
          # show in legend: main track
          'maintrack': maintrack,
          'time_zone': tz,
          'selected_layer': layer,
          'dev_site': dev,
          'unit': unit,

          'wind10': wind10,

          'is_authenticated' : request.user.is_authenticated,
          'basepath' : getenv(CERA_ENV, 'CERA_BASE_PATH', '')      # cera website (htdocs) base directory (/cera/ or /cera_risk/)

        })


#################################################################################################
# adcircrun description (info): [host]/cerarisk/adcircrun/id=1/dev=0/asgs=nc.desc
def getadcircrundesc(request, id, dev, asgs):

    adminmode = False
    if (request.META.has_key('CERA_ADMINMODE') and request.META['CERA_ADMINMODE'] != "0"):
        adminmode = True

    if len(id) > 0:
        allinfos = adcrun_info.objects.filter(id=id)
        if len(allinfos) > 0:
            requested_info = allinfos[0]

    # return...(templates/adcrun_description.html),{arbitrary name to be used in html template : variable name})
    return render_to_response('adcrun_description.html',
        { 'requested_info': requested_info, 'dev': dev, 'asgs': asgs })

###############################################################################
# convert given time (milliseconds since 1/1/1970) into a different timezone
def convert_timezone(ms, dest_tz, src_tz):

    def total_milliseconds(delta):
        return ((delta.days * 3600 * 24 + delta.seconds) * 1e6 + delta.microseconds) / 1000

    d = src_tz.localize(datetime.utcfromtimestamp(ms / 1000))

    dest = d.astimezone(dest_tz)
    dest = dest_tz.normalize(dest)

    ref = datetime(1970, 1, 1).replace(tzinfo=dest_tz)
    ref = dest_tz.normalize(ref)

    ref -= dest.dst()

    return total_milliseconds(dest - ref)

###############################################################################
# convert the embedded timestamps in the given (JSON) forecast/observed data
def convert_timezone_data(data, dest_tz, src_tz):
    data['pointStart'] = convert_timezone(data['pointStart'], dest_tz, src_tz)
    return data

# convert the embedded timestamps in the given (JSON) advisory data
def convert_timezone_advdata(data, dest_tz, src_tz):
    data[0]['x'] = convert_timezone(data[0]['x'], dest_tz, src_tz)
    return data

#####################################
# http://host/cerarisk/adcircrun/day=[day]/time=[time]/id=[id]/stationid=xxxxxxxx/cls=1/tz=utc/unit=ft/data_host=[data_host]/dev=1.html
# dev: 1=DEV, 2=PRO, 3=STATIONS
def gethydro(request, day, time, id, stationid, cls, tz, data_host, dev, unit):

    # retrieve all data for station_id
    station = None

    cls = long(cls)
    dev_site = dev
    response = 'nogageinfo.html'

    forecast_data = None
    observed_data = None
    advisory_data = None
    vert_grid_datum = ''
    vertical_datum_gage_zero = ''
    orig_station_datum = ''
    time_zone = ''
    advisory_ms = None
    error = ''
    min_chart = 0
    max_chart = 0
    maxval = 0
    maxval_ms = None
    to_grid_vert_datum_ft = 0
    storm = None
    realtimeurl = ''
    status = ''
    vdatum = ''
    navd_to_msl = None
    selected_tz = None

    dt = datetime.strptime(day, "%Y%m%d")
    t = datetime.strptime(time, "%H%M")
    dt = dt + timedelta(seconds=t.hour*3600+t.minute*60)

    dest_tz = get_pytz_timezone(tz)
    dt = as_timezone(dest_tz.localize(dt), pytz.utc)

    day = dt.strftime("%Y%m%d")
    time = dt.strftime("%H%M")

    # no forwarding script needed because direct html link in hydro chart (therefore also no data_host needed)
    download_url = 'http://%s/cgi-cera/download_hydro_single.cgi?day=%s&time=%s&com=%s&stationid=%s' % (
        data_host, day, time, id, stationid)

    url = 'day=' + day + '&time=' + time + '&id=' + id + '&stationid=' + stationid + '&dev=' + dev_site
    if cls != 6:
        try:
            # Python 2.6 allows to specify timeout=...[s]
            server = ''
            if request.META.has_key('MAPSERVER_WMSHOST'):
               server = request.META['MAPSERVER_WMSHOST']

            if len(data_host) > 0:
                server = data_host
            conn = httplib.HTTPConnection(server)
            conn.request('GET', '/cgi-cera/chart_json.cgi?' + url)
            r = conn.getresponse()
            if (r.status == 200):
                try:
                    import json
                except Exception, e:
                    import simplejson as json   # Python V2.5 has no json module

                d = json.loads(r.read())

                # time zone as given on url
                time_zone = tz.upper()
                # extract timezone
                if d.has_key('forecast_data'):
                  pointstarttime = dest_tz.localize(datetime.utcfromtimestamp(d['forecast_data']['pointStart'] / 1000))
                elif d.has_key('observed_data'):
                  pointstarttime = dest_tz.localize(datetime.utcfromtimestamp(d['observed_data']['pointStart'] / 1000))
                selected_tz = datetime.strftime(pointstarttime, '%Z')

                src_tz = get_pytz_timezone('UTC')

                if d.has_key('forecast_data'):
                    forecast_data = json.dumps(convert_timezone_data(d['forecast_data'], dest_tz, src_tz))
                if d.has_key('observed_data'):
                    observed_data = json.dumps(convert_timezone_data(d['observed_data'], dest_tz, src_tz))
                if d.has_key('advisory_data'):
                    advisory_data = json.dumps(convert_timezone_advdata(d['advisory_data'], dest_tz, src_tz))
                vert_grid_datum = d['vert_grid_datum']
                vertical_datum_gage_zero = d['vertical_datum_gage_zero']
                if d.has_key('orig_station_datum'):
                    orig_station_datum = d['orig_station_datum']
                if d.has_key('advisory_ms'):
                    advisory_ms = convert_timezone(d['advisory_ms'], dest_tz, src_tz)
                min_chart = d['min']
                max_chart = d['max']
                if d.has_key('maxval') and d.has_key('maxval_ms'):
                    maxval = d['maxval']
                    maxval_ms = convert_timezone(d['maxval_ms'], dest_tz, src_tz)
                to_grid_vert_datum_ft = d['to_grid_vert_datum_ft']
                if d.has_key('storm'):
                    storm = d['storm']
                if d.has_key('status'):
                    status = d['status']
                if d.has_key('vdatum'):
                    vdatum = d['vdatum']
                if d.has_key('navd_to_msl'):
                    navd_to_msl = d['navd_to_msl']

                response = 'gageinfo.html'

            else:
                error = str(r)

        except Exception, e:
            error = str(e)
            pass

    stations = hydro.objects.all().filter(stationid=stationid)
    if len(stations) > 0:
        station = stations[0]

        realtimeurl = station.realtimeurl
        if station.agency == 'NOAA_NOS' or station.agency == 'TCOON' or station.agency == 'PRSN':
            datum = orig_station_datum
            if datum == 'NAVD88':
                datum = 'NAVD'
            realtimeurl = realtimeurl + '&datum=%s' % (datum)

    requested_infos = adcrun_info.objects.all().filter(id=id)
    if len(requested_infos) > 0:
        requested_info = requested_infos[0]

    # return...(templates/gageinfo.html),{arbitrary name to be used in html template : variable name})
    return render_to_response(response, {
        'station': station,
        'realtimeurl': realtimeurl,
        'forecast_data': forecast_data,
        'observed_data': observed_data,
        'advisory_data': advisory_data,
        'vert_grid_datum': vert_grid_datum,
        'vert_datum_gage_zero': vertical_datum_gage_zero,
        'orig_station_datum': orig_station_datum,
        'time_zone': time_zone,
        'unit': unit,
        'advisory_ms': advisory_ms,
        'min': min_chart,
        'max': max_chart,
        'maxval': maxval,
        'maxval_ms': maxval_ms,
        'to_grid_vert_datum_ft': to_grid_vert_datum_ft,
        'storm': storm,
        'status': status,
        'vdatum': vdatum,
        'navd_to_msl':navd_to_msl,
        'error': error,
        'cls': cls,
        'requested_info': requested_info,
        'dev': dev_site,
        'selected_tz': selected_tz,
        'download_url': download_url,
        'basepath' : getenv(CERA_ENV, 'CERA_BASE_PATH', '')      # cera website (htdocs) base directory (/cera/ or /cera_risk/)

    })

#####################################
# http://host/cerarisk/adcircrun/day=[day]/time=[time]/id=[id]/stationid=xxxxxxxx/tz=utc/data_host=[data_host].html
def getprec(request, day, time, id, stationid, tz, data_host):

    # retrieve all data for precipitation stationid
    station = None

    response = 'noprecinfo.html'

    observed_data = None
    advisory_data = None
    time_zone = ''
    advisory_ms = None
    error = ''
    min_chart = 0
    max_chart = 0
    maxval = 0
    maxval_ms = None
    start = None
    # end = None
    observed_days = None
    total_48h = None
    total_24h = None
    total_6h = None
    total_hindcast = None
    storm = None

    dt = datetime.strptime(day, "%Y%m%d")
    t = datetime.strptime(time, "%H%M")
    dt = dt + timedelta(seconds=t.hour*3600+t.minute*60)

    dest_tz = get_pytz_timezone(tz)
    dt = as_timezone(dest_tz.localize(dt), pytz.utc)

    day = dt.strftime("%Y%m%d")
    time = dt.strftime("%H%M")

    url = 'day=' + day + '&time=' + time + '&id=' + id + '&stationid=' + stationid
    try:
        # Python 2.6 allows to specify timeout=...[s]
        server = ''
        if request.META.has_key('MAPSERVER_WMSHOST'):
            server = request.META['MAPSERVER_WMSHOST']

        if len(data_host) > 0:
            server = data_host
        conn = httplib.HTTPConnection(server)
        conn.request('GET', '/cgi-cera/chart_prec_json.cgi?' + url)
        r = conn.getresponse()
        if (r.status == 200):
            try:
                import json
            except Exception, e:
                import simplejson as json   # Python V2.5 has no json module

            d = json.loads(r.read())

            # time zone as given on url (e.g., tz=cdt) to display data correctly for asgs time zone
            time_zone = tz.upper()

            src_tz = get_pytz_timezone('UTC')

            if d.has_key('observed_data'):
                observed_data = json.dumps(convert_timezone_data(d['observed_data'], dest_tz, src_tz))
            if d.has_key('advisory_data'):
                advisory_data = json.dumps(convert_timezone_advdata(d['advisory_data'], dest_tz, src_tz))
            if d.has_key('advisory_ms'):
                advisory_ms = convert_timezone(d['advisory_ms'], dest_tz, src_tz)
            min_chart = d['min']
            max_chart = d['max']
            start = d['start']
            # end = d['end']
            observed_days = d['observed_days']
            if d.has_key('maxval') and d.has_key('maxval_ms'):
                maxval = d['maxval']
                maxval_ms = convert_timezone(d['maxval_ms'], dest_tz, src_tz)
            if d.has_key('total_48h'):
                total_48h  = d['total_48h']
            if d.has_key('total_24h'):
                total_24h  = d['total_24h']
            if d.has_key('total_6h'):
                total_6h  = d['total_6h']
            if d.has_key('total_hindcast'):
                total_hindcast  = d['total_hindcast']
            storm = d['storm']
            response = 'precinfo.html'

        else:
            error = str(r)

    except Exception, e:
        error = str(e)
        pass

    stations = prec.objects.all().filter(stationid=stationid)
    if len(stations) > 0:
        station = stations[0]

    # return...(templates/precinfo.html),{arbitrary name to be used in html template : variable name})
    return render_to_response(response, {
        'station': station,
        'observed_data': observed_data,
        'advisory_data': advisory_data,
        'time_zone': time_zone,
        'start': start,
        # 'end': end,
        'observed_days': observed_days,
        'advisory_ms': advisory_ms,
        'min': min_chart,
        'max': max_chart,
        'maxval': maxval,
        'maxval_ms': maxval_ms,
        'total_48h': total_48h,
        'total_24h': total_24h,
        'total_6h': total_6h,
        'total_hindcast': total_hindcast,
        'storm': storm,
        'basepath' : getenv(CERA_ENV, 'CERA_BASE_PATH', ''),      # cera website (htdocs) base directory (/cera/ or /cera_risk/)

        'error': error # 'http://' + server + '/cgi-cera/chart_prec_json.cgi?' + url
    })

#####################################
# http://host/cerarisk/adcircrun/day=20110825/time=0600/id=1/queryid=xxxxxxxx/query=elev/layer=maxelev/timestep=20110825T0900/tz=utc/unit=ft/data_host=[data_host].html
def getquery(request, day, time, id, queryid, query, layer, timestep, tz, unit, data_host):

    query_data = None
    max_layer = None
    advisory_data = None
    advisory_ms = None
    time_zone = ''
    error = ''
#    min_chart = 0
#    max_chart = 0
    maxval = None
    maxval_ms = None
    minval = None
    minval_ms = None
    #name: query group name
    name = None
    layername = None
    cls = None
    timestep_ms = None
    timestep_date = None
    timestep_value = None
    bathymetry = None
    runstart_year = None
    requested_info = None
    selected_tz = None

    dest_tz = get_pytz_timezone(tz)

    response = 'query.html'

#    dt = datetime.strptime(day, "%Y%m%d")
#    t = datetime.strptime(time, "%H%M")
#    dt = dt + timedelta(seconds=t.hour*3600+t.minute*60)
#    dt = as_timezone(dest_tz.localize(dt), pytz.utc)

    url = 'day=' + day + '&time=' + time + '&id=' + id + '&queryid=' + queryid + '&query=' + query + '&layername=' + layer + '&timestep=' + timestep + '&tz=' + tz + '&unit=' + unit
    if len(queryid) > 0:
        try:
            # Python 2.6 allows to specify timeout=...[s]
            server = ''
            if request.META.has_key('MAPSERVER_WMSHOST'):
               server = request.META['MAPSERVER_WMSHOST']

            if len(data_host) > 0:
                server = data_host
            conn = httplib.HTTPConnection(server)
            conn.request('GET', '/cgi-cera/query_json.cgi?' + url)
            r = conn.getresponse()
            if (r.status == 200):
                try:
                    import json
                except Exception, e:
                    import simplejson as json   # Python V2.5 has no json module

                d = json.loads(r.read())

                # time zone as given on url (e.g., tz=cdt) to display data correctly for asgs time zone
                time_zone = tz.upper()
                src_tz = get_pytz_timezone('UTC')

                if d.has_key('query_data'):
                  query_data = json.dumps(convert_timezone_data(d['query_data'], dest_tz, src_tz))

                  # extract timezone
                  pointstarttime = dest_tz.localize(datetime.utcfromtimestamp(d['query_data']['pointStart'] / 1000))
                  selected_tz = datetime.strftime(pointstarttime, '%Z')

#                if d.has_key('advisory_data'):
#                    advisory_data = json.dumps(convert_timezone_advdata(d['advisory_data'], dest_tz, src_tz))
#                if d.has_key('advisory_ms'):
#                    advisory_ms = convert_timezone(d['advisory_ms'], dest_tz, src_tz)
#                min_chart = d['min']
#                max_chart = d['max']
                if d.has_key('max_layer'):
                    max_layer = d['max_layer']
                if d.has_key('maxval') and d.has_key('maxval_ms'):
                    maxval = d['maxval']
                    maxval_ms = convert_timezone(d['maxval_ms'], dest_tz, src_tz)
                if d.has_key('minval') and d.has_key('minval_ms'):
                    minval = d['minval']
                    minval_ms = convert_timezone(d['minval_ms'], dest_tz, src_tz)
                if d.has_key('timestep_ms'):
                    timestep_ms = d['timestep_ms']
                    # timestep_ms is in UTC but not time-aware
                    # fromtimestamp expects a tz, otherwise it converts to local time
                    # convert timestep_ms to utc to get correct date
                    timestep_date = dest_tz.localize(datetime.utcfromtimestamp(d['timestep_ms'] / 1000))
                    timestep_value = d['timestep_value']
                if d.has_key('name'):
                    name = d['name']
                if d.has_key('layername'):
                    layername = d['layername']
                if d.has_key('cls'):
                    cls = d['cls']
                if d.has_key('bathymetry'):
                    bathymetry = d['bathymetry']
                if d.has_key('runstart'):
                    runstart_year = d['runstart'][0:4]

#                if query == "grid":
#		    response = 'querybathy.html'
#                else:
#                    response = 'query.html'

                if d.has_key('query_data') or d.has_key('max_layer'):
                  response = 'query.html'
                  error = str(d)

                else:
                  response = 'noquery.html'

            else:
                response = 'noquery.html'
                error = str(r)

            error = server + '/cgi-cera/query_json.cgi?' + url

        except Exception, e:
            error = str(e) # + str(d)
            pass

    requested_infos = adcrun_info.objects.all().filter(id=id)
    if len(requested_infos) > 0:
        requested_info = requested_infos[0]

    return render_to_response(response, {
            'query_data': query_data,
            'advisory_data': advisory_data,
            'advisory_ms': advisory_ms,
            'max_layer': max_layer,
            'time_zone': time_zone,
            'selected_tz': selected_tz,
            'unit': unit,
    #       'min': min_chart,
    #       'max': max_chart,
            'maxval': maxval,
            'maxval_ms': maxval_ms,
            'minval': minval,
            'minval_ms': minval_ms,
            'timestep_ms': timestep_ms,
            'timestep_date': timestep_date,
            'timestep_value': timestep_value,
            'name': name,
            'layername': layername,
            'cls': cls,
            'bathymetry': bathymetry,
            'queryid': queryid,
            'error': error,
            'requested_info': requested_info,
            'url': url,
            # to filter hypothetical runs (2222)
            'runstart_year':runstart_year,
            'basepath' : getenv(CERA_ENV, 'CERA_BASE_PATH', ''),      # cera website (htdocs) base directory (/cera/ or /cera_risk/)

    })

#####################################
# query outside model domain
# http://host/cerarisk/adcircrun/query_outsidedomain
def outsidedomain(request):

    response = 'query_outsidedomain.html'
    return render_to_response(response)

#####################################
# look if the CERA server is allowed to run the ASGS run from the given ADCIRC host
# http://host/cerarisk/adcircrun/adcirchost=queenbee.loni.org/cerahost=LA5.html
def filter_cera_server(request, adcirchost, cerahost):

    status = False

    info = filter_ceraserver.objects \
        .filter(adcirc_datahost=adcirchost) \
        .filter(cera_datahost=cerahost) \
        .filter(active=True)

    if len(info) > 0:
        status = True

    return render_to_response('filter_ceraserver.html', { 'status': status })

#####################################
# decides whether the complete CERA worklow (for nc_ng/pro) or the limited workflow (pub) will be executed on the given CERA server -> cera.process.py
# http://host/cerarisk/adcircrun/adcirchost=queenbee.loni.org/cerahost=LA5.workflow
def filter_cera_workflow(request, adcirchost, cerahost):

    status = False

    info = filter_ceraserver.objects \
        .filter(adcirc_datahost=adcirchost) \
        .filter(cera_datahost=cerahost) \
        .filter(pro_model_run=True)

    if len(info) > 0:
        status = True

    return render_to_response('filter_cera_workflow.html', { 'status': status })

#####################################
# filter the execution of ASGS runs by grid and track (set in table 'filter_asgs' in DB)
# use full grid name
# http://host/cerarisk/adcircrun/grid=LA_v12h-WithUpperAtch/track=t01.html
def filter_asgs_runs(request, grid, track):

    g = grid
    status = False

    info = filter_asgs.objects.filter(grid=g)
    if len(info) > 0:
        # use existing record from db
        thisinfo = info[0]
        if track == 'daily':
            status = thisinfo.daily
        elif track == 't01':
            status = thisinfo.stormt01
        elif track == 't02':
            status = thisinfo.stormt02
        elif track == 't03':
            status = thisinfo.stormt03
        elif track == 't04':
            status = thisinfo.stormt04
        elif track == 't05':
            status = thisinfo.stormt05
        elif track == 't06':
            status = thisinfo.stormt06
        elif track == 't07':
            status = thisinfo.stormt07
        elif track == 't08':
            status = thisinfo.stormt08
        elif track == 't14':
            status = thisinfo.stormt14
        elif track == 't15':
            status = thisinfo.stormt15
        elif track == 't88':
            status = thisinfo.stormt88

    return render_to_response('filter_asgs.html', { 'status': status })

#################################################################################################
# filldb_create_id
# do not name any DateTime URL key like an existing model name
# datetimes will be interpreted as UTC (no tz needed on URL)
# http://[host]/cerarisk/adcircrun/daytime=2011082506/daytimecera=2011082509/end=2011083006/grid=nc6b/windmodel=vortex-nws319/surfheight=0.22814/h0=0.1/msboundflux=27.5cms/msboundid=01160/atboundflux=27.5cms/atboundid=03465/asgsinst=rencidaily/adcirchost=blueridge.renci.org/ncpu=960/trackid=1/audience=developers-only/pub=0_1.filldb

def filldb_id_helper(request, daytime, daytimecera, end, grid, windmodel, surfheight, h0, msboundflux, msboundid, atboundflux, atboundid, asgsinst, adcirchost, ncpu, trackid, audience, pub):

    start_dt = datetime.strptime(daytime, "%Y%m%d%H").replace(tzinfo=utc)

    if len(daytimecera) > 0:
        startcera_dt = datetime.strptime(daytimecera, "%Y%m%d%H").replace(tzinfo=utc)
    else:
        startcera_dt = start_dt

    end_dt = None
    if len(end) > 0:
        end_dt = datetime.strptime(end, "%Y%m%d%H").replace(tzinfo=utc)

    # set all parameters which are optional and defined as 'CharField' to ''
    # (PostGresql stores empty string values as '' not as NULL)

    # will be used to find an existing record
    windmod = ''
    if len(windmodel) > 0:
        windmod = windmodel

    # optional - only for info button
    surf = ''
    if len(surfheight) > 0:
        surf = surfheight

    # optional - only for info button
    minwater = ''
    if len(h0) > 0:
        minwater = h0

    # optional - only for info button
    msflux = ''
    if len(msboundflux) > 0:
        msflux = msboundflux
    msid = ''
    if len(msboundid) > 0:
        msid = msboundid
    atflux = ''
    if len(atboundflux) > 0:
        atflux = atboundflux
    atid = ''
    if len(atboundid) > 0:
        atid = atboundid

    # optional - for info button and Model select box on DEV site
    inst = ''
    if len(asgsinst) > 0:
        inst = asgsinst

    # optional - only for info button
    adchost = ''
    if len(adcirchost) > 0:
        adchost = adcirchost
    cpu = ''
    if len(ncpu) > 0:
        cpu = ncpu

    # decides whether the record is included in the filtering for DEV site
    aud = ''                  # is set to 'developers-only' if empty in run.properties
    if len(audience) > 0:
        aud = audience

    # trackid is an optional parameter (if empty = no storm)
    # try to find the track
    thistrack = None
    storm_year = None

    if len(trackid) > 0:
        tracks = track.objects.filter(id=trackid).select_related('advisory__storm__year')
        if len(tracks) > 0:
            # use existing record from db
            thistrack = tracks[0]
            storm_year = thistrack.advisory.storm.year.year

    id = -1

    # try to find adcrun_info for the given start time and corresponding run info attributes
    # it is assumed that runs with different optional parameters (surfheight, h0, boundary type, boundary flux, adchosts have also different asgs_instances

    # separate by asgs_instance only for DEV site
    if audience == "developers-only":
        infos = adcrun_info.objects \
               .filter(adcrun_daytime_utc=start_dt) \
               .filter(adcrun_enddaytime_utc=end_dt) \
               .filter(grid=grid) \
               .filter(windmodel=windmod) \
               .filter(asgs_instance=inst)
    else:
        if pub == '1': #run for public website (limited data)
            infos = adcrun_info.objects \
                   .filter(adcrun_daytime_utc=start_dt) \
                   .filter(adcrun_enddaytime_utc=end_dt) \
                   .filter(grid=grid) \
                   .filter(windmodel=windmod) \
                   .filter(asgs_pub=True)
        else: #run for pro/nc/ng website (full data)
            infos = adcrun_info.objects \
                   .filter(adcrun_daytime_utc=start_dt) \
                   .filter(adcrun_enddaytime_utc=end_dt) \
                   .filter(grid=grid) \
                   .filter(windmodel=windmod) \
                   .filter(asgs_pub=False)

    if len(trackid) > 0:
        infos = infos.filter(track_id=trackid)
    else:
        infos = infos.filter(track_id=None)

    if len(infos) == 0:
        # this run info does not exist, create a new one
        thisinfo = adcrun_info()
        thisinfo.adcrun_daytime_utc = start_dt
        thisinfo.adcrun_daytime_cera = startcera_dt
        thisinfo.adcrun_enddaytime_utc = end_dt
        thisinfo.grid = grid
        # sets the grid_datum, init_grid_datum is defined in models.py
        thisinfo.init_grid_datum()
        thisinfo.windmodel = windmod
        thisinfo.surfheight = surf
        thisinfo.h0 = minwater
        thisinfo.msboundflux = msflux
        thisinfo.msboundid = msid
        thisinfo.atboundflux = atflux
        thisinfo.atboundid = atid
        thisinfo.asgs_instance = inst
        thisinfo.adcirc_datahost = adchost
        thisinfo.ncpu = cpu
        thisinfo.track_id = thistrack   	# assign the entire instance, not only the id
        if len(trackid) > 0:
            thisinfo.has_adv = True
        else:
            thisinfo.has_adv = False
        thisinfo.enable_adminmode = True
        thisinfo.enable_public = False          # this will later be overwritten by filldb_layerinfo
        thisinfo.program_version = 8

        if storm_year is not None:
            if storm_year > 90000:
                thisinfo.is_pseudo = True

        thisinfo.save(force_insert=True)
        id = thisinfo.id
        status = 'created'
        data_host = 'unknown'
    else:
        # use existing record from db
        thisinfo = infos[0]

        if storm_year is not None:
            if storm_year >= 90000 and not thisinfo.is_pseudo:
                thisinfo.is_pseudo = True
                thisinfo.save(force_update=True)

            elif storm_year < 90000 and thisinfo.is_pseudo:
                thisinfo.is_pseudo = False
                thisinfo.save(force_update=True)

        id = thisinfo.id
        status = 'exists'
        data_host = thisinfo.get_wmsserver_display()

    # set sequence_nr for multiple runs if the only different parameter is the asgs_instance
    # re-filter because new object might have been added
#    infoseq = adcrun_info.objects \
#               .filter(adcrun_daytime_utc=start_dt) \
#               .filter(adcrun_enddaytime_utc=end_dt) \
#               .filter(grid=grid) \
#               .filter(windmodel=windmod)

#    if len(infoseq) > 1:
#        seq_list = []
#        for inf in infoseq:
#            seq = inf.sequence_nr
            # if the run that is not the current run doesn't got a sequence_nr assigned yet (is still 'None'), set it to '1'
            # this should only happen the first time (if one run exists with seqnr None and a second run comes in with a different asgs_instance)
#            if seq is None:
#                if inf.id != thisinfo.id:
                    # set seqnr to '1' for the first run in the DB
#                    seq = 1
#                    inf.sequence_nr = 1
#                    inf.save(force_update=True)
#                else:
#                    seq = 0
#            if seq not in seq_list:
#                seq_list.append(seq)

#        seq_list.sort(reverse=True)
#        seqnr = seq_list[0] + 1
#        if thisinfo.sequence_nr is None:
#            thisinfo.sequence_nr = seqnr
#            thisinfo.save(force_update=True)

    # returned id value will be used to fill the metafile, do not change the template
    return render_to_response('filldb_id.html', \
        { 'id': id, 'status': status, 'data_host': data_host })


@transaction.atomic
def filldb_id(request, daytime, daytimecera, end, grid, windmodel, surfheight, h0, msboundflux, msboundid, atboundflux, atboundid, asgsinst, adcirchost, ncpu, trackid, audience, pub):

    # repeat until filldb succeeds
    while True:
        try:
            with transaction.atomic():
                return filldb_id_helper(request, daytime, daytimecera, end, grid, windmodel, \
                    surfheight, h0, msboundflux, msboundid, atboundflux, atboundid, \
                    asgsinst, adcirchost, ncpu, trackid, audience, pub)

        except IntegrityError:
            continue


#####################################
# 'filldb_asgs': associate an asgs_system with an existing 'adcrun_info' ID depending on 'intendedAudience'
# set legend according to asgs_system in run.properties (geographic region of the storm)
# http://[host]/cerarisk/adcircrun/id=6/asgs=nc/audience=general/globmesh=0_1/pub=0_1.filldb
# the script will never be called via the web app with an empty initial URL (day=/time=/id=.html); the day/time info is therefore not needed on the URL

def filldb_asgs(request, id, asgs, audience, globmesh, pub):

    info = adcrun_info.objects.filter(id=id)
    if (len(info) == 0):
        return render_to_response('filldb_asgs.html', { 'asgs': 'adcrun_info id not found' })

    thisinfo = info[0]

    need_update = False

    if not asgs in ['pro', 'pub', 'ng', 'nc', 'pr', 'ri', 'pl', 'st', 'dev']:
        return render_to_response('filldb_asgs.html', { 'asgs': 'unknown asgs system' })

    asgs_db = asgs

    # set ASGS-DEV if IntendedAudience = 'developers-only' and set all other instances to False
    if audience == 'developers-only':
        if not thisinfo.asgs_dev:
            thisinfo.asgs_dev = True
            need_update = True
        if thisinfo.asgs_pro:
            thisinfo.asgs_pro = False
            need_update = True
        if thisinfo.asgs_pub:
            thisinfo.asgs_pub = False
            need_update = True
        if thisinfo.asgs_nc:
            thisinfo.asgs_nc = False
            need_update = True
        if thisinfo.asgs_ng:
            thisinfo.asgs_ng = False
            need_update = True
        if thisinfo.asgs_pr:
            thisinfo.asgs_pr = False
            need_update = True
        if thisinfo.asgs_st:
            thisinfo.asgs_st = False
            need_update = True

        # exception asgs:ri (will always be posted to CERA-RI independent from audience)
        if asgs == 'ri':
            if thisinfo.asgs_dev:
                thisinfo.asgs_dev = False
                need_update = True
            if not thisinfo.asgs_ri:
                thisinfo.asgs_ri = True
                need_update = True

        # set asgs name for returned template
        if asgs != 'ri':
            asgs_db = 'dev'

    else: #audience:general or professional

        ########################
        # set PUB (is only allowed for nc/ng/(pr) + audience:general + pub=1 (mesh = PUB_MESH from cera_define.py))
        # status is set in filldb_create_id.py
        # if pub is valid, all other system are set to False
        if pub == '1':
            if not thisinfo.asgs_pub:
                thisinfo.asgs_pub = True
                need_update = True
            if thisinfo.asgs_dev:
                thisinfo.asgs_dev = False
                need_update = True
            if thisinfo.asgs_pro:
                thisinfo.asgs_pro = False
                need_update = True
            if thisinfo.asgs_nc:
                thisinfo.asgs_nc = False
                need_update = True
            if thisinfo.asgs_ng:
                thisinfo.asgs_ng = False
                need_update = True
            if thisinfo.asgs_pr:
                thisinfo.asgs_pr = False
                need_update = True
            if thisinfo.asgs_st:
                thisinfo.asgs_st = False
                need_update = True

        else:
            if thisinfo.asgs_pub:
                thisinfo.asgs_pub = False
                need_update = True

            # set always ASGS-PRO
            # exception: asgs:ri (will always be posted to CERA-RI independent from audience)
            # exception: pub (will only be posted to pub)
            if asgs == 'ri':
                if thisinfo.asgs_pro:
                    thisinfo.asgs_pro = False
                    need_update = True
            else: #nc/ng/pr
                if not thisinfo.asgs_pro:
                    thisinfo.asgs_pro = True
                    need_update = True

            ########################
            if audience == 'general':   # asgs is either nc/ng/pr

                ######################
                if asgs == 'nc':
                    if not thisinfo.asgs_nc:
                        thisinfo.asgs_nc = True
                        need_update = True

                    # globmesh=1 means that the GLOBMESH entry in defines.py is set to the same grid as the grid used in the actual run
                    # globmesh=1 + intendedAudience=general checks all asgs systems (nc/ng/pro)
                    if thisinfo.asgs_ng:
                        if globmesh == '0':
                            thisinfo.asgs_ng = False
                            need_update = True
                    else:
                        if globmesh == '1':
                            thisinfo.asgs_ng = True
                            need_update = True

                    if thisinfo.asgs_pr:
                        thisinfo.asgs_pr = False
                        need_update = True
                    if thisinfo.asgs_ri:
                        thisinfo.asgs_ri = False
                        need_update = True

                elif asgs == 'ng':
                    if not thisinfo.asgs_ng:
                        thisinfo.asgs_ng = True
                        need_update = True

                    if thisinfo.asgs_nc:
                        if globmesh == '0':
                            thisinfo.asgs_nc = False
                            need_update = True
                    else:
                        if globmesh == '1':
                            thisinfo.asgs_nc = True
                            need_update = True

                    if thisinfo.asgs_pr:
                        thisinfo.asgs_pr = False
                        need_update = True
                    if thisinfo.asgs_ri:
                        thisinfo.asgs_ri = False
                        need_update = True

                elif asgs == 'pr':
                    if not thisinfo.asgs_pr:
                        thisinfo.asgs_pr = True
                        need_update = True
                    if thisinfo.asgs_nc:
                        thisinfo.asgs_nc = False
                        need_update = True
                    if thisinfo.asgs_ng:
                        thisinfo.asgs_ng = False
                        need_update = True
                    if thisinfo.asgs_ri:
                        thisinfo.asgs_ri = False
                        need_update = True

                elif asgs == 'ri':
                    if not thisinfo.asgs_ri:
                        thisinfo.asgs_ri = True
                        need_update = True
                    if thisinfo.asgs_nc:
                        thisinfo.asgs_nc = False
                        need_update = True
                    if thisinfo.asgs_ng:
                        thisinfo.asgs_ng = False
                        need_update = True
                    if thisinfo.asgs_pr:
                        thisinfo.asgs_pr = False
                        need_update = True

                else:
                    return render_to_response('filldb_asgs.html', { 'asgs': 'unknown asgs system' })

            # professional
            else:
                if thisinfo.asgs_nc:
                    thisinfo.asgs_nc = False
                    need_update = True
                if thisinfo.asgs_ng:
                    thisinfo.asgs_ng = False
                    need_update = True
                if thisinfo.asgs_ri:
                    thisinfo.asgs_ri = False
                    need_update = True
                if thisinfo.asgs_pr:
                    thisinfo.asgs_pr = False
                    need_update = True

    #########################
    # set correct legend
    if asgs == 'nc' or asgs == 'ri':
        if thisinfo.grid_datum == 'msl':
            if thisinfo.legend != 'nc':
                thisinfo.legend = 'nc'
                need_update = True
        else:
            if thisinfo.legend != 'nc_navd':
                thisinfo.legend = 'nc_navd'
                need_update = True
    elif asgs == 'ng':
        if thisinfo.legend != 'ng':
            thisinfo.legend = 'ng'
            need_update = True
    elif asgs == 'pr':
        if thisinfo.legend != 'pr':
            thisinfo.legend = 'pr'
            need_update = True

    else:
        return render_to_response('filldb_asgs.html', { 'asgs': 'unknown asgs system' })

    if need_update:
        thisinfo.save(force_update=True)

    return render_to_response('filldb_asgs.html', { 'asgs': asgs_db })

#####################################
# 'filldb_website_region': add the website region (nc/ng/nc_ng) (geographic region of the storm) to an an existing 'adcrun_info' ID
# for storm with a global mesh (hsofs/ec95d)  use the orig_asgs system from the run.proprties to set the region
# http://[host]/cerarisk/adcircrun/id=6/orig_asgs=nc/globmesh=0/1.filldb

def filldb_website_region(request, id, orig_asgs, globmesh):

    info = adcrun_info.objects.filter(id=id)
    if (len(info) == 0):
        return render_to_response('filldb_website_region.html', { 'region': 'adcrun_info id not found' })

    thisinfo = info[0]

    need_update = False

    if not thisinfo.asgs_dev and not thisinfo.asgs_pro and not thisinfo.asgs_pub and not thisinfo.asgs_nc \
        and not thisinfo.asgs_ng and not thisinfo.asgs_st and not thisinfo.asgs_pr and not thisinfo.asgs_ri:
        return render_to_response('filldb_website_region.html', { 'region': 'no asgs system given' })

    if thisinfo.asgs_pr:
        if thisinfo.website_region != 'pr':
            thisinfo.website_region = 'pr'
            need_update = True

    if thisinfo.asgs_ri:
        if thisinfo.website_region != 'ri':
            thisinfo.website_region = 'ri'
            need_update = True

    # no region map setting for PUB only (always nc_ng)
#    if thisinfo.asgs_pub and not thisinfo.asgs_ng and not thisinfo.asgs_nc:
#        if thisinfo.website_region != 'nc_ng':
#            thisinfo.website_region = 'nc_ng'
#            need_update = True

    # no region map setting for DEV/ST
#    if thisinfo.asgs_dev or thisinfo.asgs_st:
#        if thisinfo.website_region != 'nc_ng':
#            thisinfo.website_region = 'nc_ng'
#            need_update = True

    ########################################
    # should not occur other than for globmesh daily runs but better test it
#    if thisinfo.asgs_nc and thisinfo.asgs_ng:
#        if thisinfo.website_region != 'nc_ng':
#            thisinfo.website_region = 'nc_ng'
#            need_update = True

    #hsofs/ec95d
    if globmesh == '1':
        #daily runs
        if not thisinfo.has_adv:
            if thisinfo.website_region != 'nc_ng':
                thisinfo.website_region = 'nc_ng'
                need_update = True
        #storms
        else:
            if orig_asgs == 'nc':
                if thisinfo.website_region != 'nc':
                    thisinfo.website_region = 'nc'
                    need_update = True
            elif orig_asgs == 'ng':
                if thisinfo.website_region != 'ng':
                    thisinfo.website_region = 'ng'
                    need_update = True

    if thisinfo.asgs_nc and not thisinfo.asgs_ng:
        if thisinfo.website_region != 'nc':
            thisinfo.website_region = 'nc'
            need_update = True

    if thisinfo.asgs_ng and not thisinfo.asgs_nc:
          if thisinfo.website_region != 'ng':
              thisinfo.website_region = 'ng'
              need_update = True

    if thisinfo.asgs_pro and not thisinfo.asgs_ng and not thisinfo.asgs_nc:
        if orig_asgs == 'nc':
            if thisinfo.website_region != 'nc':
                thisinfo.website_region = 'nc'
                need_update = True
        elif orig_asgs == 'ng':
            if thisinfo.website_region != 'ng':
                thisinfo.website_region = 'ng'
                need_update = True


    if need_update:
        thisinfo.save(force_update=True)

    return render_to_response('filldb_website_region.html', { 'region': thisinfo.website_region })


#####################################
# filldb_storminfo
# do not name any URL key like an existing model name!
# datetimes will be interpreted as UTC (no tz needed on URL)
# http://[host]/cerarisk/adcircrun/year=2010/stormnr=07/stormname=EARL/firstadv=2011082312/adv=31/stormcls=HURRICANE/cat=4/tracknr=t06/percent=20/advtime=201108231200.filldb

# year, stormnr, adv, track, advtime are 'must' parameters, all other (optional parameters) will be tested for existence
# datetimes will be interpreted as UTC
def filldb_storm(request, year, stormnr, stormname, firstadv, adv, stormcls, cat, tracknr, percent, advtime):

    firstadv_dt = None
    if len(firstadv) > 0:
        firstadv_dt = datetime.strptime(firstadv, "%Y%m%d%H").replace(tzinfo=utc)

    stormclass = None
    if len(stormcls) > 0:
        stormclass = stormcls

    category = None
    if len(cat) > 0:
        category = cat

    advtime_dt = None
    if len(advtime) > 0:
        advtime_dt = datetime.strptime(advtime, "%Y%m%d%H%M").replace(tzinfo=utc)

    thistrack = create_storm_records(year, stormnr, stormname, firstadv_dt, adv, stormclass, category, advtime_dt, tracknr, percent)

    #returned value will be used to fill the metafile - do not put anything else in the template
    return render_to_response('filldb_storm.html', { 'id': thistrack.id })

#####################################
# filldb_lastadv
# do not name any URL key like an existing model name!
# times will be interpreted as UTC (no tz needed on URL)
# http://[host]/cerarisk/adcircrun/trackid=1/lastadv=2011082312.filldb

def filldb_lastadv(request, trackid, lastadv):

    if len(lastadv) > 0:
      lastadv_dt = datetime.strptime(lastadv, "%Y%m%d%H").replace(tzinfo=utc)

    if len(trackid) > 0:
      # try to find the trackid in 'track'
      track_info = track.objects.filter(id=trackid)
      # use existing record from 'track'
      thistrack = track_info[0]
      advid = thistrack.advisory.id

    # try to find the advid in 'advisory'
    adv_info = advisory.objects.filter(id=advid)
    # use existing record from 'advisory'
    thisadv = adv_info[0]
    stormid = thisadv.storm.id

    # try to find the stormid in 'storm'
    storm_info = storm.objects.filter(id=stormid)
    # use existing record from 'storm'
    thisstorm = storm_info[0]

    status = 'unknown'
    need_update = False
#    if len(lastadv) > 0 and thisstorm.last_date_utc != lastadv_dt:
    # lastadv in storm.bal is not always correct and manually corrected in the DB, do not overwrite
    if len(lastadv) > 0 and thisstorm.last_date_utc == None:
      thisstorm.last_date_utc = lastadv_dt
      need_update = True
    if need_update:
      thisstorm.save(force_update=True)
      status = 'created'

    return render_to_response('filldb_lastadv.html', { 'lastadv': status })

#####################################
# filldb_subtrack
# do not name any URL key like an existing model name!
# times will be interpreted as UTC (no tz needed on URL)
# http://[host]/cerarisk/adcircrun/id=1/trackid=1.filldb

def filldb_subtrack(request, id, trackid):

  if len(id) == 0 or len(trackid) == 0:
    return render_to_response('filldb_subtrack.html', { 'status': 'id or trackid not given on url' })

  subtracks = subtrack.objects \
    .filter(adcrunid=id) \
    .filter(trackid=trackid)

  status = 'exists'

  if len(subtracks) == 0:
    infos = adcrun_info.objects.filter(id=id)
    if len(infos) == 0:
      return render_to_response('filldb_subtrack.html', { 'status': 'id not found' })

    # try to find the trackid in 'track'
    track_infos = track.objects.filter(id=trackid)
    if len(track_infos) == 0:
      return render_to_response('filldb_subtrack.html', { 'status': 'trackid not found' })

    sub_track = subtrack()
    sub_track.adcrunid = infos[0]
    sub_track.trackid = track_infos[0]

    sub_track.save(force_insert=True)
    status = 'created'

  return render_to_response('filldb_subtrack.html', { 'status': status })

#####################################
# check if the run is set as default_view (to send out email only for these runs)
# use full grid name
# http://host/cerarisk/adcircrun/id=1.default_view
def check_default_view(request, id):

    default_view = False

    info = adcrun_info.objects.filter(id=id)
    thisinfo = info[0]
    if thisinfo.default_view:
        default_view = True

    return render_to_response('default_view.html', { 'default_view': default_view })

#####################################
# filldb_layer_info; fill the available layer info, set 'show_layer' to True by default, set the wmsserver, enable the 'public webserver', set the 'default_view'
# http://[host]/cerarisk/adcircrun/id=6/layer=maxelev/start=2011082506/end=2011083006/wmsserver=NC2.filldb
# layer output start and end times are only for maxhist layers and are given in UTC (no tz needed on URL)
# the script will never be called via the web app with an empty initial URL (day=/id=.html); the day/time info is therefore not needed on the URL

#if a tag is given on the URL like 'has_layer=0|1'
#def get_flag(field):
#    if (field == '1'):
#        return True
#    return False

def filldb_data(request, id, layer, wmsserver):

    info = adcrun_info.objects.filter(id=id)
    if len(info) == 0:
        return render_to_response('filldb_layer.html', { 'status': 'id not found' })

    thisinfo = info[0]

    # try to find existing record via 'thisinfo.id' in 'layerinfo'
    layer_info = layerinfo.objects \
                     .filter(adcrun_info=thisinfo.id) \
                     .filter(layername=layer)

#    show_layer = get_flag(has_layer)

    if len(layer_info) == 0:
        # 'layerinfo' does not exist in db, create a new one
        thislayer = layerinfo()
        thislayer.adcrun_info = thisinfo
        thislayer.layername = layer
        thislayer.show_layer = True
#        thislayer.layer_output_start = start_dt
#        thislayer.layer_output_end = end_dt
        thislayer.save(force_insert=True)

        status = 'created'

    else:
        # update existing record with each new run
        thislayer = layer_info[0]
        if thislayer.show_layer is False:
            thislayer.show_layer = True

        # optional start/end times may need to get upddated with each new run
#        need_update = False
#        if len(start) > 0 and thislayer.layer_output_start != start_dt:
#            thislayer.layer_output_start = start_dt
#            need_update = True
#        if len(end) > 0 and thislayer.layer_output_end != end_dt:
#            thislayer.layer_output_end = end_dt
#            need_update = True
#        if need_update:
#           thislayer.save(force_update=True)

        status = 'existing'

    if thisinfo.wmsserver != wmsserver:
        thisinfo.wmsserver = wmsserver
        # nr_cacheserver is dependent on wmsserver, set_nr_cacheserver is defined in models.py
        thisinfo.set_nr_cacheserver()
        thisinfo.save(force_update=True)

        status = 'updated'

    # set as default_view (according to mesh settings in table 'filter_asgs', do not set for side tracks)
    grid = filter_asgs.objects.filter(grid = thisinfo.grid)

    default_from_track = False
    if thisinfo.track_id is None or thisinfo.track_id.track == 't01':
        default_from_track = True

    thisgrid = None
    if default_from_track and len(grid) > 0:
        thisgrid = grid[0]

        if thisinfo.asgs_ng and thisinfo.asgs_nc:
            if thisgrid.default_view_pro:
                thisinfo.default_view = True
                thisinfo.save(force_update=True)
        else:
            if thisinfo.asgs_ng:
                if thisgrid.default_view_ng:
                    thisinfo.default_view = True
                    thisinfo.save(force_update=True)
            if thisinfo.asgs_nc:
                if thisgrid.default_view_nc:
                    thisinfo.default_view = True
                    thisinfo.save(force_update=True)

        if not thisinfo.asgs_ng and not thisinfo.asgs_nc and not thisinfo.asgs_pr and not thisinfo.asgs_ri and thisinfo.asgs_pro:
            if thisgrid.default_view_pro:
                thisinfo.default_view = True
                thisinfo.save(force_update=True)

        status = 'updated'

    if not thisinfo.enable_public:
        thisinfo.enable_public = True
        thisinfo.save(force_update=True)

    return render_to_response('filldb_layer.html', { 'status': status, 'thisinfo': thisinfo, 'thisgrid': thisgrid })

################################################################################
# http://[host]/cerarisk/adcircrun/id=6/asgs=nc.emailsubject
def emailsubject_nostorm(request, id, asgs):

    info = adcrun_info.objects.filter(id=id)
    thisinfo = info[0]

    # no asgs in subject line for CERA 2018 anymore but still needed for timezone
    return render_to_response('notification/notification_subject.txt', {
        "info": thisinfo, "asgs": asgs
    })

################################################################################
# email no storm and websites DEV/RI/PR (independent)
# http://[host]/cerarisk/adcircrun/id=1/asgs=dev.emailtext
def emailtext_nostorm(request, id, asgs):

    info = adcrun_info.objects.filter(id=id)
    thisinfo = info[0]

    # page: http://host/cerarisk?cera=devcom=%s
    link_dev = "http://cera-dev.coastalrisk.live?com=%s" % thisinfo.id
    # page: http://host/cerarisk?cera=pr&com=%s
    link_pr = "http://cera-pr.coastalrisk.live?com=%s" % thisinfo.id
    # page: http://host/cerarisk?cera=ri&com=%s
    link_ri = "http://cera-ri.coastalrisk.live?com=%s" % thisinfo.id

    # requires login and proper user permission
    # page: http://host/cerarisk?cera=pro/nc_ng&com=%s
    link_cera = "http://cera.coastalrisk.live?com=%s" % thisinfo.id

    return render_to_response('notification/notification.txt', {
      "info": thisinfo, "asgs": asgs,
      "link_dev": link_dev, "link_pr": link_pr, "link_ri": link_ri, "link_cera": link_cera
    })

################################################################################
# http://[host]/cerarisk/adcircrun/id=6/asgs=nc/rapid=0|1.emailsubjectstorm
# CERAv6: rapid=1 means the RAPID results email (notification_storm_subject_v6.txt)
# CERAv7: all storm emails sent out as rapid results
def emailsubject_storm(request, id, asgs, rapid):

    info = adcrun_info.objects.filter(id=id)
    thisinfo = info[0]

    return render_to_response('notification/notification_storm_subject.txt', {
        "info": thisinfo, "asgs": asgs, "rapid": rapid
    })

################################################################################
# http://[host]/cerarisk/adcircrun/id=6/asgs=nc/rapid=0|1.emailtextstorm
# CERAv6: rapid=1 means the RAPID results email (Notification_storm_v6.txt)
# CERAv7: all storm emails sent out as rapid results
def emailtext_storm(request, id, asgs, rapid):

    info = adcrun_info.objects.filter(id=id)
    thisinfo = info[0]

    # page: http://host/cerarisk?cera=devcom=%s
    link_dev = "http://cera-dev.coastalrisk.live?com=%s" % thisinfo.id
    # page: http://host/cerarisk?cera=pr&com=%s
    link_pr = "http://cera-pr.coastalrisk.live?com=%s" % thisinfo.id
    # page: http://host/cerarisk?cera=ri&com=%s
    link_ri = "http://cera-ri.coastalrisk.live?com=%s" % thisinfo.id

    # requires login and proper user permission
    # page: http://host/cerarisk?cera=pro/nc_ng&com=%s
    link_cera = "http://cera.coastalrisk.live?com=%s" % thisinfo.id

    return render_to_response('notification/notification_storm.txt', {
      "info": thisinfo, "asgs": asgs, "rapid": rapid ,
      "link_dev": link_dev, "link_pr": link_pr, "link_ri": link_ri, "link_cera": link_cera
    })

################################################################################
# parse GTWO Invest xml files (invest_tooltip.xml)
def parse_invest(request, id, investnr, perc, cat):

    if len(id) > 0:
        allinfos = adcrun_info.objects.filter(id=id)

        # check if id exists
        if len(allinfos) > 0:
             requested_info = allinfos[0]

             daytime = requested_info.adcrun_daytime_utc
             year = datetime.strftime(daytime, "%Y")
             month = datetime.strftime(daytime, "%m")
             day = datetime.strftime(daytime, "%d")
             hour = datetime.strftime(daytime, "%H")
             id = requested_info.id

             f = open("%s/%s/%s/%s/%s/%s/track_invest/invest_tooltip.xml" % (WMS_DIR, year, month, day, hour, id), 'r')
             data = f.read()
             f.close()
             xmldoc = minidom.parseString(data)

             desc = ''
             for i in xmldoc.getElementsByTagName("item"):
                 t = i.getElementsByTagName("title")
                 if len(t) > 0:
                     if t[0].childNodes[0].nodeValue == 'NHC Atlantic Outlook':

                         for d in i.getElementsByTagName("description"):
                             for d_val in d.childNodes:
                                 desc += d_val.data

                             break

                 if len(desc) == 0:
                     return render_to_response('notooltip_invest.html')
             import re

             # until July 2014
             # <decription> tag in invest_tooltip.xml has <a name = ''> tags which end with a double break,
             # group 0= entire text within <description>, group1= <a> tag, group2(WANTED)= text after <a> tag, group4= <br/><br/>
#             invest = re.search('(<a name="%s"></a>(.*?))(<br ?/>.){2}' % investnr, desc, re.IGNORECASE | re.DOTALL)

#             if invest is None:
#                 return render_to_response('notooltip_invest.html')

#             if len(invest.groups()) < 3:
#                 return render_to_response('notooltip_invest.html')

#             desc = invest.group(2).replace("<br />", "")
#             desc = desc.replace("\n", "<br />")
#             return render_to_response('tooltip_invest.html', { "desc": desc, "perc": int(perc), "cat": cat })

             # 2015
             # <decription> tag in invest_tooltip.xml contains text "For the North Atlantic...Caribbean Sea and the Gulf of Mexico:"
             # which ends with a double break, then start the invest description sections, each with '<investnr>. ' (e.g. '1. '
             # group 0= entire text within <description>, group1= double break, group2 (WANTED)= text after 1: (or 2: ...) , group3= <br/><br/>
             invest = re.search('(<br ?/>.){2}(%s. (.*?))(<br ?/>.){2}' % investnr, desc, re.IGNORECASE | re.DOTALL)
             if invest is None:
                 return render_to_response('notooltip_invest.html')

             if len(invest.groups()) < 3:
                 return render_to_response('notooltip_invest.html')

             desc = invest.group(2).replace("<br />", "")
             desc = desc.replace("\n", "<br />")
             #desc = invest.group(2)
             return render_to_response('tooltip_invest.html', { "desc": desc, "perc": int(perc), "cat": cat })

        else:
             return render_to_response('notooltip_invest.html')

    return render_to_response('notooltip_invest.html')

################################################################################
# return trackpoint tooltip html template file (will be filled with jquery later)
def create_tooltip_trackpoint(request, trackid):

    if len(trackid) > 0:
        alltracks = track.objects.filter(id=int(trackid))

        # check if id exists
        if len(alltracks) > 0:
            requested_track = alltracks[0]

            return render_to_response('tooltip_trackpoint.html', {
            "stormname": requested_track.advisory.storm.stormname,
            "advisory": requested_track.advisory.advisory
             })

        else:
             return render_to_response('notooltip_trackpoint.html')

    return render_to_response('notooltip_trackpoint.html')

#################################################################################################
# deliver legend image
def getlegendimg(request, id, layer):
    # url: http://[host]/cerarisk/adcircrun/id=<id>/layer=<layername>.legend
    from django.conf import settings
    from django.http import Http404

    #legendimg: <layer>_<has_adv>(_<basin>).png
    img_name = ''

    if len(id) > 0:
        allinfos = adcrun_info.objects.filter(id=id)

        # check if id exists
        if len(allinfos) > 0:
            requested_info = allinfos[0]

            # try to find record via 'requestd_info.id' and layername in 'layerinfo'
            all_layers = layerinfo.objects \
                     .filter(adcrun_info=requested_info.id) \
                     .filter(layername=layer)

            # check if layername exists for run
            if len(all_layers) > 0:
                thislayer = all_layers[0]

                # check if show_layer is True
                if thislayer.show_layer:
                    if layer == 'elev' or layer == 'maxelev':
                        img_layername = 'elev'
                    if layer == 'inun' or layer == 'maxinun':
                        img_layername = 'inun'
                    if layer == 'hsign' or layer == 'maxhsign':
                        img_layername = 'hsign'
                    if layer == 'tps' or layer == 'maxtps':
                        img_layername = 'tps'
                    if layer == 'wvel' or layer == 'maxwvel':
                        img_layername = 'wvel'
                else:
                    raise Http404

            else:
                raise Http404

            # storm status and basin
            if requested_info.has_adv:
                img_storm = '_storm'

                # get basin
                if img_layername == 'elev' or img_layername == 'inun' or img_layername == 'hsign':
                    if requested_info.legend == 'nc' or requested_info.legend == 'pr':
                        img_basin = "_atlantic"
                    else:
                        img_basin = "_gulf"
                else:
                    img_basin = ''

            else:
                img_storm = '_nostorm'
                img_basin = ''

            # get vertical datum
            if img_layername == 'elev' or img_layername == 'hsign':
                if requested_info.grid_datum == 'msl':
                    img_datum = '_msl'
                else:
                    img_datum = '_navd'
            else:
                img_datum = ''

            # final png image name
            img_name = "%s%s%s%s.png" % (img_layername, img_storm, img_basin, img_datum)

            file_path = 'legendimg/%s' % img_name
            # relative to settings.py
            fp = open(os.path.join(settings.PROJECT_ROOT, file_path), 'rb')
            response = HttpResponse(fp.read())
            fp.close()
            #import mimetypes
            #encoding = mimetypes.guess_type(filename)
            type = 'image/png'
            response['Content-Type'] = type
            #if encoding is not None:
            #  response['Content-Encoding'] = encoding
            #filename_header = 'filename*=UTF-8\'\'%s' % urllib.quote(filename.encode('utf-8'))
            #response['Content-Disposition'] = filename_header
            return response

        else:
            raise Http404
    else:
        raise Http404

#    return render_to_response('legendimg.test', {
#                   "id": requested_info.id, 'layer': thislayer.layername, 'img_name': img_name
#    })


