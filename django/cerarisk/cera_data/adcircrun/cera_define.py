# script to define all parameters that are relevant to post-process an ASGS run for CERA 
#
# Copyright (c) 2006-2018 Carola Kaiser, Louisiana State University
# Distributed under the Boost Software License, Version 1.0. 
# See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)

import os

# set email settings for download META; this is only for the initial download of the run.properties
# sending out the final CERA results uses a separate email address

# incoming ASGS emails
EMAIL_ACCOUNT = "asgs.cera.lsu@gmail.com"
EMAIL_PASSWORD = "storm23surge@#"
# SCP download from mike.hpc.lsu.edu etc.
SCP_USER = 'cera'

#warning and error messages
INTERNAL_EMAIL_TO = ["ckaiser@cct.lsu.edu"]

# email notifications (the system will be set in notification.py)
EMAIL_NOSTORM_TO = {
  "ng": ("ckaiser@cct.lsu.edu"),
  "nc": ("ncfs_dev@renci.org"),
  "pro": ("ckaiser@cct.lsu.edu"),     
  "dev": ("ckaiser@cct.lsu.edu"),
#  "dev": ("ckaiser@cct.lsu.edu", "jason.fleming@seahorsecoastal.com", "natedill@gmail.com"),
#  "dev": ("cera_results_dev@cct.lsu.edu"),
  "pr": ("ckaiser@cct.lsu.edu"),
  "ri": ("ckaiser@cct.lsu.edu")
#  "ri": ("ckaiser@cct.lsu.edu", "xychen@my.uri.edu","iginis@uri.edu","jason.fleming@seahorsecoastal.com" )
}

EMAIL_STORM_TO = {
  # subscribers on both lists but not pro
  "nc_ng": ("ckaiser@cct.lsu.edu"),
#  "nc_ng": ("cera_results@cct.lsu.edu"),
  "nc": ("ckaiser@cct.lsu.edu"),
#  "nc": ("nccera_results@cct.lsu.edu"),
  "ng": ("ckaiser@cct.lsu.edu"),
#  "ng": ("ngcera_results@cct.lsu.edu"),
  "pro": ("ckaiser@cct.lsu.edu"),
#  "pro": ("cera_results_pro@cct.lsu.edu"),   
  "dev": ("ckaiser@cct.lsu.edu")
#  "dev": ("ckaiser@cct.lsu.edu", "jason.fleming@seahorsecoastal.com", "natedill@gmail.com")
#  "dev": ("cera_results_dev@cct.lsu.edu")
}

# No storm, audience: general
FINAL_EMAIL_TO = [ "ckaiser@cct.lsu.edu" ]
# No storm, audience: professional
FINAL_EMAIL_PRO_TO = [ "ckaiser@cct.lsu.edu" ]
# No storm, audience: developers-only
FINAL_EMAIL_DEV_TO = [ "ckaiser@cct.lsu.edu" ]
#FINAL_EMAIL_DEV_TO = [ "ckaiser@cct.lsu.edu", "jason.fleming@seahorsecoastal.com", "natedill@gmail.com" ]

#storm, audience: general
#FINAL_STORM_EMAIL_TO = [ "cera_results@cct.lsu.edu", "ngcera_results@cct.lsu.edu", "nccera_results@cct.lsu.edu", "cera_results_pro@cct.lsu.edu" ]
FINAL_STORM_EMAIL_TO = [ "ckaiser@cct.lsu.edu" ]
# storm, audience: professional
#FINAL_STORM_EMAIL_PRO_TO = [ "cera_results_pro@cct.lsu.edu" ]
FINAL_STORM_EMAIL_PRO_TO = [ "ckaiser@cct.lsu.edu" ]
# storm, audience: developers-only
FINAL_STORM_EMAIL_DEV_TO = [ "ckaiser@cct.lsu.edu" ]
#FINAL_STORM_EMAIL_DEV_TO = [ "ckaiser@cct.lsu.edu","jason.fleming@seahorsecoastal.com" ]

# RI: all runs
FINAL_EMAIL_RI_TO = [ "ckaiser@cct.lsu.edu"]
#FINAL_EMAIL_RI_TO = [ "ckaiser@cct.lsu.edu","xychen@my.uri.edu","iginis@uri.edu","jason.fleming@seahorsecoastal.com" ]

#outgoing CERA emails
MSG_FROM = "cera.results@gmail.com"
EMAIL_IN_SERVER = "pop.gmail.com"
EMAIL_OUT_SERVER = "smtp.gmail.com"
EMAIL_PORT = "587"

# flag in google mail to mark an existing run with the DATA_HOST
EMAIL_TAG = 'twister'

#'temp' folder to hold all data for post-processing (content will be deleted or archived after success)
TEMP_DIR = "I:/CERA/temp"

#metadata file
META = "run.properties"
#logfile name
LOG = "log.txt"

# the AUDIENCE decides about the meshes that are allowed on the Client website (cera=nc_ng with login)
# for the allowed meshes the intendedAudience in the run.properties is set to 'general'
# 'general' checkes the asgs_ng/asgs_nc fields in the DB
# The public website is pub. The script filldb_create_id parses the key PUB_MESH. 
# If this mesh matches the grid for the current run and is set in AUDIENCE, the asgs system pub is checked in the DB.

# 'ri' is always posted to CERA-RI website, audience is secondary
PUB_MESH = 'hsofs'
AUDIENCE = {
  "ng": ('hsofs','LAv17a','tx2008','ocprv19',None),
  "nc": ('hsofs','NCv999riv','FEMAR2_2012','FEMAR3','NAC2014'),
  "pr": ('prv01',None,None,None,None)
}
# this grid will be checked as nc/ng/pro if grid is defined in AUDIENCE
GLOBMESH = ('hsofs', 'ec95d')

#archive directory for original emails
ARC_EMAIL = "I:/CERA/archives/archive_emails"
#ADCIRC run archive directory
ARC_DIR = "I:/CERA/archives/archive_adcircruns"

#wms_data directory for data-processing
WMS_HOST = "http://twister.cct.lsu.edu"
WMSSERVER = "LA2"
WMS_DIR = "I:/CERA/wms_data"

#TileCache
#cfg for tilecache creation on working drive
CFG = "cera_wms_process.cfg"
#create Tilecache on working drive(s)
CACHE_DRIVE = 'I'
ALT_CACHE_DRIVE = 'I'
CACHE_PATH = "CERA/wms_data/tilecache"
#web display Tilecache directory
CACHE_DIR_WEB = "I:/CERA/wms_data/tilecache"

# internal ftp directory on data_host
FTP_DIR = "I:/CERA/ftp_data"
#DOWNL_DESCR = {
#  "nc": "CERA_Download_File_Description_Atlantic.pdf",
#  "ng": "CERA_Download_File_Description_Northern_Gulf.pdf",
#  "pr": "CERA_data_format_description_PuertoRico.txt"
#}

# shapefile polygons
SHPPOLY_DESCR = {
  "nc": "CERA_shapefile_polygons_description_Atlantic.pdf",
  "ng": "CERA_shapefile_polygons_description_Northern_Gulf.pdf",
  "pr": "CERA_data_format_description_PuertoRico.txt"
}
# shapefile polygons
SHPPOINTS_DESCR = {
  "nc": "CERA_shapefile_points_description_Atlantic.pdf",
  "ng": "CERA_shapefile_points_description_Northern_Gulf.pdf"
}
# public FTP server
FTP_SERVER = "galaxy.ngi.lsu.edu"
FTP_USER = 'cera_upload'

DJANGOPATH = "twister.cct.lsu.edu/cerarisk/adcircrun"

#program paths for CERA data-processing
SCRIPT_DIR = "I:/CERA/programs/"
CONFIG_DIR = "I:/CERA/programs/configfiles"
#fort.15
CONFIG_15_DIR = "I:/CERA/programs/configfiles/netcdf2ascii"

TRACKFILENAME = "fort.cera.22"

ASGS_TIMEZONE = {
  "ng": "CDT",
  "nc": "EDT",
  "pr": "AST",
  "ri": "EDT"
}

# map (color) files for SHPs (since CERA version 6)
MAPFILE_NOSTORM = "I:/CERA/wms_data/cera_wms_nostorm.map"
MAPFILE_NG = "I:/CERA/wms_data/cera_wms_ng.map"
MAPFILE_NC = "I:/CERA/wms_data/cera_wms_nc.map"

#maximum extent to draw WMS/WFS layers
MAPEXTENT = [ -110.0, 0.0, -50.0, 60.0 ]

# configuration files for ascii2netcdf.exe
ATT_TXT = "I:/CERA/programs/configfiles/ascii2netcdf/generic_atts.txt"

#programs (which will be directly called from a *.py script (not imported as module)
ASCII2NETCDF_RENCI = "I:/CERA/programs/ascii2netcdf_renci.exe"
ASCII2NETCDF = "I:/CERA/programs/ascii2netcdf.exe"
NETCDF2ASCII = "I:/CERA/programs/netcdf2ascii.exe"
# SHP (contour) creation
CONTOUR = "I:/CERA/programs/contour.py"
# TIF creation
ADCIRCMAP = "I:/CERA/programs/adcircmap.exe"
ADCIRCMAP_TIMESTEPS = "I:/CERA/programs/adcircmap_timesteps.py"
# query
ADCIRCSHP = "I:/CERA/programs/adcircshp.exe"
ADCIRCSHP_TIMESTEPS = "I:/CERA/programs/adcircshp_timesteps.py"
STORM_TRACK_GEN = "I:/CERA/programs/storm_track_gen.pl"
GENERATE_TRACK = "I:/CERA/programs/track_shape.py"
INVEST_TRACK = "I:/CERA/programs/invest_track_shape.py"
TILECACHE_SEED = "I:/CERA/programs/tilecache_seed.py"
PARSE_ADV = "I:/CERA/programs/nhc_advisory_bot.pl"
PRED_HYDRO = "I:/CERA/programs/adcirchydrographs.exe"
PRED_HYDRO2 = "I:/CERA/programs/extract_station_data.py"
REALTIME_HYDRO = "I:/CERA/programs/realtime_hydrographs.py"
HYDRO2CSV = "I:/CERA/programs/station_transpose.pl"
REALTIME_PREC = "I:/CERA/programs/realtime_precip.py"
CREATE_CHARTS = "I:/CERA/programs/chart_data_hydro.py"
CREATE_CHARTS_VAL = "I:/CERA/programs/chart_data_hydro_validation.py"
CREATE_CHARTS_PREC = "I:/CERA/programs/chart_data_precip.py"

SHPTREE = "C:/ms4w/Apache/cgi-bin/shptree.exe"
WGETPATH = "C:/cygwin/bin/wget.exe"
GZIPPATH = "C:/cygwin/bin/gzip.exe"
PYTHONPATH = "C:/Python27/python.exe"
PYTHONPATH64 = "C:/Python27_64/python.exe"
PERLPATH = "C:/perl/bin/perl.exe"
PSFTP = "I:/CERA/programs/psftp.exe"

ARCHIVE_HOST = "http://galaxy.ngi.lsu.edu"
# data directory for archived INVEST files on INVEST_HOST
INVEST_DIR = "C:/ms4w/Apache/cera_invest_data"
# data directory for archived DAT/FST files on INVEST_HOST
TRACK_DIR = "C:/ms4w/Apache/cera_track_data"