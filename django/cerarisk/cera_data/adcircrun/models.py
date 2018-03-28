from pytz import timezone, utc
from datetime import datetime, timedelta

from django.db import models
from django.contrib.auth.models import User
from localflavor.us.us_states import STATE_CHOICES
from localflavor.us.models import USStateField
#from phonenumber_field.modelfields import PhoneNumberField
from localflavor.us.models import PhoneNumberField

from django.db.models.signals import post_save
from django.db.models.signals import post_delete
from django.db.models.signals import pre_save

from django.template.loader import render_to_string

#from notification import send_notifications, send_storm_notifications

###############################################################################
#data access permission (cera.json file)
USER_PERMISSION = (
  ("pub", "pub"),
  ("nc_ng", "nc_ng"),
  ("pro", "pro")
)

class UserProfile(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE)
  organization = models.CharField(default='', max_length=100, blank=True)
  job_title = models.CharField(default='', max_length=100, blank=True)
  city = models.CharField(max_length=50, default='', blank=True)
  state = USStateField(choices=STATE_CHOICES, default='', blank=True)
  phone = PhoneNumberField(default='', blank=True)
  cera = models.CharField('User permission', max_length=5, choices=USER_PERMISSION, default='nc_ng')

  def __str__(self):
    return self.user.username

  class Meta:
    verbose_name = "User Profile"
    ordering = ['user__username']

def create_profile(sender, **kwargs):
  if kwargs ['created']:
    user_profile = UserProfile.objects.create(user=kwargs['instance'])

###############################################################################
class storm_year(models.Model):

  id = models.AutoField('ID', primary_key=True, unique=True)
  year = models.IntegerField()

  dependent_enable_public_dev = models.BooleanField(default=False)
  dependent_enable_public_pro = models.BooleanField(default=False)
  dependent_enable_public_pub = models.BooleanField(default=False)
  dependent_enable_public_ng = models.BooleanField(default=False)
  dependent_enable_public_nc = models.BooleanField(default=False)
  dependent_enable_public_pr = models.BooleanField(default=False)
  dependent_enable_public_ri = models.BooleanField(default=False)
  dependent_enable_public_st = models.BooleanField(default=False)
  dependent_enable_adminmode_dev = models.BooleanField(default=True)
  dependent_enable_adminmode_pro = models.BooleanField(default=True)
  dependent_enable_adminmode_pub = models.BooleanField(default=True)
  dependent_enable_adminmode_ng = models.BooleanField(default=True)
  dependent_enable_adminmode_nc = models.BooleanField(default=True)
  dependent_enable_adminmode_pr = models.BooleanField(default=True)
  dependent_enable_adminmode_ri = models.BooleanField(default=True)
  dependent_enable_adminmode_st = models.BooleanField(default=True)
  dependent_asgs_dev = models.BooleanField(default=False)
  dependent_asgs_pro = models.BooleanField(default=False)
  dependent_asgs_pub = models.BooleanField(default=False)
  dependent_asgs_nc = models.BooleanField(default=False)
  dependent_asgs_ng = models.BooleanField(default=False)
  dependent_asgs_pr = models.BooleanField(default=False)
  dependent_asgs_ri = models.BooleanField(default=False)
  dependent_asgs_st = models.BooleanField(default=False)
  dependent_region_nc_ng = models.BooleanField(default=False)
  dependent_region_nc = models.BooleanField(default=False)
  dependent_region_ng = models.BooleanField(default=False)
  dependent_region_ri = models.BooleanField(default=False)
  dependent_region_pr = models.BooleanField(default=False)

  def __unicode__(self):
    return str(self.year)

  class Meta:
    #name for class
    verbose_name = "year"
    verbose_name_plural = "Storm Years"
    ordering = ['-year']

###############################################################################
class storm(models.Model):

  id = models.AutoField('ID', primary_key=True, unique=True)
  year = models.ForeignKey(storm_year, on_delete=models.CASCADE)
#  storm_number = models.IntegerField('NHC storm number', help_text='Omit leading zeros.')
  storm_number = models.CharField('NHC storm number', max_length=3, help_text='Omit leading zeros.')
  stormname = models.CharField('storm name', max_length=22, null=True, blank=True)
  start_date_utc = models.DateTimeField('First NHC advisory', help_text='Provide the first advisory in CDT date format YYYY-MM-DD and CDT time format HH:MM.', null=True, blank=True)
  last_date_utc = models.DateTimeField('Last NHC advisory', help_text='Provide the last advisory in CDT date format YYYY-MM-DD and CDT time format HH:MM.', null=True, blank=True)
  has_hindcast = models.BooleanField('storm with hindcast (has_hindcast)', default=False)

  dependent_enable_public_dev = models.BooleanField(default=False)
  dependent_enable_public_pro = models.BooleanField(default=False)
  dependent_enable_public_pub = models.BooleanField(default=False)
  dependent_enable_public_ng = models.BooleanField(default=False)
  dependent_enable_public_nc = models.BooleanField(default=False)
  dependent_enable_public_pr = models.BooleanField(default=False)
  dependent_enable_public_ri = models.BooleanField(default=False)
  dependent_enable_public_st = models.BooleanField(default=False)
  dependent_enable_adminmode_dev = models.BooleanField(default=True)
  dependent_enable_adminmode_pro = models.BooleanField(default=True)
  dependent_enable_adminmode_pub = models.BooleanField(default=True)
  dependent_enable_adminmode_ng = models.BooleanField(default=True)
  dependent_enable_adminmode_nc = models.BooleanField(default=True)
  dependent_enable_adminmode_pr = models.BooleanField(default=True)
  dependent_enable_adminmode_ri = models.BooleanField(default=True)
  dependent_enable_adminmode_st = models.BooleanField(default=True)
  dependent_asgs_dev = models.BooleanField(default=False)
  dependent_asgs_pro = models.BooleanField(default=False)
  dependent_asgs_pub = models.BooleanField(default=False)
  dependent_asgs_nc = models.BooleanField(default=False)
  dependent_asgs_ng = models.BooleanField(default=False)
  dependent_asgs_pr = models.BooleanField(default=False)
  dependent_asgs_ri = models.BooleanField(default=False)
  dependent_asgs_st = models.BooleanField(default=False)
  dependent_region_nc_ng = models.BooleanField(default=False)
  dependent_region_nc = models.BooleanField(default=False)
  dependent_region_ng = models.BooleanField(default=False)
  dependent_region_ri = models.BooleanField(default=False)
  dependent_region_pr = models.BooleanField(default=False)

  def get_storm_name(self):
    if len(self.stormname) > 0:
      return self.stormname
    return self.storm_number

  def __unicode__(self):
    return ("%s %s" % (str(self.year), self.stormname))

  class Meta:
    ordering = ['-start_date_utc']

###############################################################################
STORMCLASS_CHOICES = (
  ("db", "Disturbance"),
  ("ds", "Dissipating"),
  ("rem", "Remants"),
  ("ptc", "Potential Tropical Cyclone"),
  ("sd", "Subtropical Depression"),
  ("ss", "Subtropical Storm"),
  ("pt", "Post-Tropical Cyclone"),
  ("ex", "Extratropical System"),
  ("td", "Tropical Depression"),
  ("ts", "Tropical Storm"),
  ("hu", "Hurricane")
)

CATEGORY_CHOICES = (
  ("db", "DS"),   # Disturbance
  ("ds", "DS"),   # Dissipating
  ("rem", "REM"), # Remants
  ("ptc", "PTC"), # Potential Tropical Cyclone
  ("sd", "SD"),   # Subtropical Depression
  ("ss", "SS"),   # Subtropical Storm
  ("td", "TD"),   # Tropical Depression
  ("ts", "TS"),   # Tropical Storm
  ("pt", "PT"),   # Post-Tropical Storm
  ("ex", "EX"),   # Extratropical Systems
  ("1", "H1"),    # Hurricane 1
  ("2", "H2"),
  ("3", "H3"),
  ("4", "H4"),
  ("5", "H5")
)

class advisory(models.Model):
  id = models.AutoField('ID', primary_key=True, unique=True)
  advisory = models.CharField('NHC advisory number', max_length=3, help_text='Omit leading zeros.')
  storm = models.ForeignKey(storm, on_delete=models.CASCADE)
  stormclass = models.CharField(max_length=3, choices = STORMCLASS_CHOICES, null=True, blank=True)
  category = models.CharField(max_length=3, choices = CATEGORY_CHOICES, null=True, blank=True)
  adv_time_utc = models.DateTimeField('NHC advisory time', help_text='Provide the advisory time in CDT date format YYYY-MM-DD and CDT time format HH:MM:SS.', null=True, blank=True)

  dependent_enable_public_dev = models.BooleanField(default=False)
  dependent_enable_public_pro = models.BooleanField(default=False)
  dependent_enable_public_pub = models.BooleanField(default=False)
  dependent_enable_public_ng = models.BooleanField(default=False)
  dependent_enable_public_nc = models.BooleanField(default=False)
  dependent_enable_public_pr = models.BooleanField(default=False)
  dependent_enable_public_ri = models.BooleanField(default=False)
  dependent_enable_public_st = models.BooleanField(default=False)
  dependent_enable_adminmode_dev = models.BooleanField(default=True)
  dependent_enable_adminmode_pro = models.BooleanField(default=True)
  dependent_enable_adminmode_pub = models.BooleanField(default=True)
  dependent_enable_adminmode_ng = models.BooleanField(default=True)
  dependent_enable_adminmode_nc = models.BooleanField(default=True)
  dependent_enable_adminmode_pr = models.BooleanField(default=True)
  dependent_enable_adminmode_ri = models.BooleanField(default=True)
  dependent_enable_adminmode_st = models.BooleanField(default=True)
  dependent_asgs_dev = models.BooleanField(default=False)
  dependent_asgs_pro = models.BooleanField(default=False)
  dependent_asgs_pub = models.BooleanField(default=False)
  dependent_asgs_nc = models.BooleanField(default=False)
  dependent_asgs_ng = models.BooleanField(default=False)
  dependent_asgs_pr = models.BooleanField(default=False)
  dependent_asgs_ri = models.BooleanField(default=False)
  dependent_asgs_st = models.BooleanField(default=False)
  dependent_region_nc_ng = models.BooleanField(default=False)
  dependent_region_nc = models.BooleanField(default=False)
  dependent_region_ng = models.BooleanField(default=False)
  dependent_region_ri = models.BooleanField(default=False)
  dependent_region_pr = models.BooleanField(default=False)

  def __unicode__(self):
    return str(self.advisory)

  class Meta:
    # plural name for class
    verbose_name_plural = "Advisories and Tracks"
    ordering = ['-adv_time_utc']

###############################################################################
TRACK_CHOICES = (
  ("t01", "NHC forecast"),
  ("t02", "max wind speed"),
  ("t03", "over land speed"),
  ("t04", "veer left"),
  ("t05", "veer right"),
  ("t06", "max radius"),
  ("t07", "max wind speed only"),
  ("t08", "constant max radius"),
  ("t14", "shift left"), 
  ("t15", "shift right"), 
  # FEMA runs
  ("t88", "synthetic")
)

class track(models.Model):
  id = models.AutoField('ID', primary_key=True, unique=True)

  track = models.CharField(max_length=3, choices = TRACK_CHOICES)
  mod_percent = models.CharField('percent/miles track modification', max_length=5, null=True, blank=True, default=0)
  advisory = models.ForeignKey(advisory, on_delete=models.CASCADE)
  # at least one model run uses this track (for clickable subtracks)
  has_model_run = models.BooleanField(default=False)

  dependent_enable_public_dev = models.BooleanField(default=False)
  dependent_enable_public_pro = models.BooleanField(default=False)
  dependent_enable_public_pub = models.BooleanField(default=False)
  dependent_enable_public_ng = models.BooleanField(default=False)
  dependent_enable_public_nc = models.BooleanField(default=False)
  dependent_enable_public_pr = models.BooleanField(default=False)
  dependent_enable_public_ri = models.BooleanField(default=False)
  dependent_enable_public_st = models.BooleanField(default=False)
  dependent_enable_adminmode_dev = models.BooleanField(default=True)
  dependent_enable_adminmode_pro = models.BooleanField(default=True)
  dependent_enable_adminmode_pub = models.BooleanField(default=True)
  dependent_enable_adminmode_ng = models.BooleanField(default=True)
  dependent_enable_adminmode_nc = models.BooleanField(default=True)
  dependent_enable_adminmode_pr = models.BooleanField(default=True)
  dependent_enable_adminmode_ri = models.BooleanField(default=True)
  dependent_enable_adminmode_st = models.BooleanField(default=True)
  dependent_asgs_dev = models.BooleanField(default=False)
  dependent_asgs_pro = models.BooleanField(default=False)
  dependent_asgs_pub = models.BooleanField(default=False)
  dependent_asgs_nc = models.BooleanField(default=False)
  dependent_asgs_ng = models.BooleanField(default=False)
  dependent_asgs_pr = models.BooleanField(default=False)
  dependent_asgs_ri = models.BooleanField(default=False)
  dependent_asgs_st = models.BooleanField(default=False)
  dependent_region_nc_ng = models.BooleanField(default=False)
  dependent_region_nc = models.BooleanField(default=False)
  dependent_region_ng = models.BooleanField(default=False)
  dependent_region_ri = models.BooleanField(default=False)
  dependent_region_pr = models.BooleanField(default=False)

  def __unicode__(self):
    return "ID: %s (%s)" % (self.id, self.track)

  def get_track_info_text(self):
    if self.advisory.advisory == '999':
      return 'NHC best track'
    # 991: hindcast OWI (Irma 2017 with different start time)
    if self.advisory.advisory == '991':
      return 'best track'
    if self.track == 't01' or self.track == 't88':
      return self.get_track_display()
    if self.track != 't08':
      return "%s %s%% " % (self.get_track_display(), self.mod_percent)
    return "%s %snm" % (self.get_track_display(), self.mod_percent)

  class Meta:
    ordering = ['id']


###############################################################################
GRID_CHOICES = (
  ("cpra_2011_v03a","CPRAv3"),
  ("cpra_2017_v07a_chk","CPRA2017v07"),
  ("cpra2017_v11k-CurrentConditions_chk","CPRA2017v11"),
  ("cpra2017_v12c-CurrentConditions-WithUpperAtch_chk","CPRA2017v12"),
  ("ec95d","EC95D"),
  ("FEMA_R2_merge_VALID_correct_gcs_mNAVD","FEMAR2"),
#  ("FEMA_R2_norivers_gcs_mNAVD","FEMAR2_2016"),
  ("FEMAR3","FEMAR3"),
  ("FEMAR4", "FEMAR4"),
  ("sl15_2010_HSDRRS_2012_v9","HSDRRS"),
  ("HSDRRS2014_MRGO_leveeupdate_fixSTC_MX","HSDRRS2014"),
  ("hsofs", "HSOFS"),
  ("ULLR2D", "IOOSul"),
  ("LA_v12h-WithUpperAtch", "LAv12hAtch"),
  ("LA_v17a-WithUpperAtch_chk", "LAv17a"),
  ("LPRBv1", "LPRBv1"),
  ("NACCS_2014_r01", "NAC2014"),
  ("narragansett", "NARRA"),
  ("narragansett_bay_ec_95d_v2", "NARRA2015v2"),
  ("nc6b","NC6B"),
  ("nc_inundation_v9.99","NCv999"),
  ("nc_inundation_v9.99_w_rivers","NCv999riv"),
  ("ocpr_v19a_DesAllemands4CERA","OCPRv19"),
#  ("norl_s08_g05f_grd","S08"),
  ("prv01", "PRv01"),
  ("sl15v3_2007_r9a","SL15v3"),
  ("sl15_2007_IHNC_r03q_levchk","SL15v7"),
  ("sl16_alpha_2007_26","SL16"),
  ("tx2008r35h", "TX2008"),
  ("tx2008r35hred", "TX2008red"),
  ("wFL_v4.1.0","wFlv41"),
  ("ECIRL","ECIRL")
)

WINDMODEL_CHOICES = (
  ("fitz-nws4","FITZ Wind Scheme"),
  ("GFDL_URI", "GFDL URI"),
  # NOAA Hurricane Research Division
  ("hwind", "NOAA HWind"),
  # with background winds
  ("lsu","LSU Wind Model"),
  ("NWS-305","NWS-305"),
  ("vortex-nws308", "NWS-308"),
  # Oceanweather Inc. Fast Delivery Meteorology
  ("NWS-12","OWI NWS-12"),
  ("NWS-312","OWI NWS-312"),
  # simplified Holland B derived from from the initial tropical cyclone
  #  conditions provided by NHC and JTWC (sometimes referred to as TC vitals
  # or the TC bogus), used by RI group
  ("tc-vitals", "TC Vitals"),
  ("tides_only", "Tides only"),
  # Assymetric Holland Model
  ("vortex-nws19","AHM"),
  #version 2014 - Generalized Asymmetric Holland Model)
  ("vortex-nws20","GAHM"),
  # Asymmetric Vortex + Waves
  ("vortex-nws319","AHM+SWAN"),
  ("vortex-nws320","GAHM+SWAN"),
  ("weatherflow-nws312", "Weatherflow"),
  ("WNAMAW12-NCP","12km NAM"),
  ("WNAMAW12+NWS19","12km NAM + AHM"),
  ("WNAMAW32-NCP","32km NAM")
)

WMSSERVER_CHOICES = (
  ("NC1","nc-cera.renci.org"),
  ("NC2","nccera-2.renci.org"),
  ("LA1","cera.cct.lsu.edu"),
  ("LA2","twister.cct.lsu.edu"),
  ("LA3","jupiter.cct.lsu.edu"),
  ("LA4","juno.cct.lsu.edu"),
  ("LA5","luna.cct.lsu.edu"),
  ("LA6","apollo.cct.lsu.edu")
)

def get_data_host_display(short_name):
  for choice in WMSSERVER_CHOICES:
    if choice[0] == short_name:
      return choice[1]
  return 'unknown'

ADCIRCDATAHOST_CHOICES = (
  ("blueridge.renci.org","blueridge.renci.org"),
  ("coconut.dmes.fit.edu","coconut.dmes.fit.edu"),
  ("croatan.renci.org", "croatan.renci.org"),
  ("diamond.erdc.hpc.mil", "diamond.erdc.hpc.mil"),
  ("garnet.erdc.hpc.mil","garnet.erdc.hpc.mil"),
  ("hatteras.renci.org", "hatteras.renci.org"),
  ("lonestar.tacc.utexas.edu", "lonestar.tacc.utexas.edu"),
  ("mike.hpc.lsu.edu", "mike.hpc.lsu.edu"),
  ("MSUserver","MSU server"),
  ("queenbee.loni.org","queenbee.loni.org"),
  ("tezpur.hpc.lsu.edu","tezpur.hpc.lsu.edu"),
  ("topaz.erdc.hpc.mil", "topaz.erdc.hpc.mil"),
  ("thunder.afrl.hpc.mil", "thunder.afrl.hpc.mil")
)

MAP_REGION = (
  ("nc_ng","nc_ng"),
  ("ng","ng"),
  ("nc","nc"),
  ("pr","pr"),
  ("ri","ri")
)

LEGEND_CHOICES = (
  ("ng","Gulf"),
  ("nc","Atlantic"),
  ("pr","Puerto")
)

class adcrun_info(models.Model):

  #primary model run ID
  id = models.AutoField('ID', primary_key=True, unique=True)

  # the following fields should be many-to-many relations -> one adcrun_info can have many asgs systems and many layerinfos
  # asgs_systems = models.ManyToManyField(asgs_system)
  # layerinfos = models.ManyToManyField(layerinfo, null=True, blank=True)
  # the approach using ForeignKeys in the associated models (asgs_system and layerinfo) blows up the DB
  # but is much simpler in admin.py/views.py

  adcrun_daytime_utc = models.DateTimeField('ASGS start day and time') # asgs model start time
  # default: 3hrs after runstarttime to match advisory times
  adcrun_daytime_cera = models.DateTimeField('CERA start day and time', help_text='Normally 3 hrs after RunStartTime to match advisory time (except hindcasts).')
  adcrun_enddaytime_utc = models.DateTimeField('ASGS end day and time', null=True, blank=True)

  ### has at least one associated storm advisory or advisory 999
  has_adv = models.BooleanField('active storm (has_adv)', default=False)
  track_id = models.ForeignKey(track, verbose_name='ID track', help_text='Select the ID from the associated track', on_delete=models.CASCADE, null=True, blank=True)
  ### pseudo storm (real storm under different conditions or test/synthetic storms)
  is_pseudo = models.BooleanField('pseudo', default=False)

  windmodel = models.CharField('wind model', max_length=25, null=True, blank=True, choices=WINDMODEL_CHOICES)
  grid =  models.CharField('Grid', max_length=50, choices=GRID_CHOICES)
  grid_datum =  models.CharField('grid datum', max_length=4)
  # 'Model Info' select box: default is windmodel/grid (function 'get_model_info_text'
  # for multiple runs on DEV site, the asgs_instance will be added
  asgs_instance = models.CharField('ASGS instance', max_length=25, null=True, blank=True)
  # adcrun identifier for equal runs except description or adcirc_datahost (developer/professional/stations page)
  sequence_nr = models.IntegerField('Sequence Nr.', null=True, blank=True)
  # info button
  description = models.CharField(null=True, blank=True, max_length=500)
  surfheight = models.CharField('Sea Surface Height', null=True, blank=True, max_length=10)
  h0 = models.CharField('H0', null=True, blank=True, max_length=6)
  msboundflux = models.CharField('MS Boundary Flux', null=True, blank=True, max_length=10)
  msboundid = models.CharField('MS Boundary GageID', null=True, blank=True, max_length=25)
  atboundflux = models.CharField('AT Boundary Flux', null=True, blank=True, max_length=10)
  atboundid = models.CharField('AT Boundary GageID', null=True, blank=True, max_length=25)
  ncpu= models.CharField('Number CPU', null=True, blank=True, max_length=5)
  remark = models.CharField(null=True, blank=True, max_length=300)

  enable_public = models.BooleanField('Enable public web server', default=False)
  enable_adminmode = models.BooleanField('Enable admin display', default=True)
  program_version = models.IntegerField('Program version', default=8)
  ### original data host (ADCRIC/SWAN data)
  adcirc_datahost = models.CharField('ADCIRC data host', max_length=30, null=True, blank=True, choices=ADCIRCDATAHOST_CHOICES)
  ### data_host (tif, wfs data)
  wmsserver = models.CharField('CERA data host', max_length=4, null=True, blank=True, choices=WMSSERVER_CHOICES)
  ### tilecache
  nr_cacheserver = models.IntegerField('CERA cache hosts', default=0)

  asgs_dev = models.BooleanField('ASGS-DEV', default=False)
  asgs_pro = models.BooleanField('ASGS-PRO', default=False)
  asgs_pub = models.BooleanField('ASGS-PUB', default=False)
  asgs_nc = models.BooleanField('ASGS-NC', default=False)
  asgs_ng = models.BooleanField('ASGS-NG', default=False)
  asgs_pr = models.BooleanField('ASGS-PR', default=False)
  asgs_ri = models.BooleanField('ASGS-RI', default=False)
  asgs_st = models.BooleanField('ASGS-ST', default=False)

  # show this run as default when multiple runs are available with the same starttime
  default_view = models.BooleanField('Default view', default=False)

  # ocean basin that triggers the nc/ng/nc_ng map settings on the website
  website_region = models.CharField('Website region', max_length=5, null=True, blank=True, choices=MAP_REGION)
  #show correct legend images
  legend = models.CharField(max_length=7, choices=LEGEND_CHOICES)

  def set_nr_cacheserver(self):
    if self.wmsserver == "LA1" or self.wmsserver == "NC1" or self.wmsserver == "NC2" or self.wmsserver == "LA3" or self.wmsserver == "LA4" or self.wmsserver == "LA5" or self.wmsserver == "LA6":
      self.nr_cacheserver = 4
    else:
      self.nr_cacheserver = 0

  def init_grid_datum(self):
    if self.grid in ("nc6b", "nc_inundation_v9.99", "nc_inundation_v9.99_w_rivers", "FEMA_R2_merge_VALID_correct_gcs_mNAVD", "FEMAR3", "ec95d", "prv01", "NAC2014_r01", "narragansett", "narragansett_bay_ec_95d_v2", "hsofs", "LPRBv1"):
      self.grid_datum = 'msl'
    else:
      self.grid_datum = 'navd'

  def grid_datum_text(self):
    if self.grid_datum == 'msl':
      return 'MSL'
    return 'NAVD88'

  def __unicode__(self):
    return "ID: %s" % self.id

  class Meta:
    verbose_name = "ADCIRC Run Info"
    verbose_name_plural = "ADCIRC Run Info"
    ordering = ['adcrun_daytime_utc']

# -----------------------------------------------------------------------------
  # model info select box for DEV site (windmodel/grid)

  def get_model_info_text_pro(self):
    windmodel = 'Unknown'
    if self.windmodel is not None:
      windmodel = self.get_windmodel_display()
    seq = ''
    if self.sequence_nr is not None:
      seq = ' (%s)' % self.sequence_nr
    return '%s / %s%s' % (windmodel, self.get_mapped_grid_display(), seq)

  def get_model_info_text_dev(self):
    windmodel = 'Unknown'
    if self.windmodel is not None:
      windmodel = self.get_windmodel_display()
#    if self.asgs_instance is not None and self.asgs_instance != '':
#      return '%s / %s (%s)' % (windmodel, self.get_mapped_grid_display(), self.asgs_instance)
    return '%s / %s' % (windmodel, self.get_mapped_grid_display())

# 'best for' select box on public pages (ng,nc,pr)
# if for selected time either only storm or only NAM run exist
  def grid_region_text(self):
    region = 'Unknown'
    if self.grid == "sl16_alpha_2007_26":
      region = "Northern Gulf"
    elif self.grid == "ec95d":
      region = "all regions - low resolution"
    elif self.grid == "ocpr_v19a_DesAllemands4CERA" or self.grid == "cpra_2011_v03a" or self.grid == "cpra_2017_v07a_chk" \
      or self.grid == "cpra2017_v11k-CurrentConditions_chk" or self.grid == "cpra2017_v12c-CurrentConditions-WithUpperAtch_chk" \
      or self.grid == "sl15v3_2007_r9a" or self.grid == "sl15_2007_IHNC_r03q_levchk" \
      or self.grid == "LA_v12h-WithUpperAtch" or self.grid == "LA_v17a-WithUpperAtch_chk":
      region = "Louisiana"
    elif self.grid == "sl15_2010_HSDRRS_2012_v9" or self.grid == "HSDRRS2014_MRGO_leveeupdate_fixSTC_MX":
      region = "East Louisiana"
    elif self.grid == "nc6b" or self.grid == "nc_inundation_v9.99" or self.grid == "nc_inundation_v9.99_w_rivers":
      region = "North Carolina"
    elif self.grid == "FEMA_R2_merge_VALID_correct_gcs_mNAVD":
      region = "New Jersey"
    elif self.grid == "FEMAR3":
      region = "Virginia/Maryland"
    elif self.grid == "FEMAR4":
      region = "Mississippi/Alabama"
    elif self.grid == "ULLR2D":
      region = "Gulf of Mexico"
    elif self.grid == "prv01":
      region = "Puerto Rico"
    elif self.grid == "tx2008r35h" or self.grid == "tx2008r35hred":
      region = "Texas"
    elif self.grid == "NACCS_2014_r01":
      region = "North Atlantic"
    elif self.grid == "narragansett" or self.grid == "narragansett_bay_ec_95d_v2":
      region = "Rhode Island"
    elif self.grid == "hsofs":
      region = "Atlantic/Gulf"
    elif self.grid == "wFL_v4.1.0":
      region = "West Florida"
    elif self.grid == "ECIRL":
      region = "East Florida"
    elif self.grid == "LPRBv1":
      region = "Lower Pearl River"

    return '%s' % region

# 'best for' select box
  # if for selected time multiple runs exist
  def grid_region1_text(self):
    region = self.grid_region_text()
    seq = ''
    if self.sequence_nr is not None:
      seq = ' (%s)' % self.sequence_nr
    return '%s%s' % (region, seq)

  # if for selected time both storm + NAM run exist
  def grid_region2_text(self):
    region = self.grid_region_text()
    seq = ''
    if self.sequence_nr is not None:
      seq = ' (%s)' % self.sequence_nr

    if self.has_adv:
      return '%s%s' % (region, seq)
    else:
      return '%s (NAM)%s' % (region, seq)

# show in select box a different name than the get_grid_display name
  def get_mapped_grid_display(self):
    mapped_name = self.get_grid_display()
    if self.grid == 'cpra_2011_v03a':
      mapped_name = 'CPRA2011'
    elif self.grid == 'ocpr_v19a_DesAllemands4CERA':
      mapped_name = 'OCPR'
    elif self.grid == 'cpra_2017':
      mapped_name = 'CPRA2017v07'
    elif self.grid == 'sl15_2010_HSDRRS_2012_v9':
      mapped_name = 'HSDRRS2012'
#    elif self.grid == 'nc_inundation_v9.99':
#      mapped_name = 'NCv999'
    elif self.grid == 'tx2008r35hred':
      mapped_name = 'TX2008reduced'
    elif self.grid == 'FEMA_R2_merge_VALID_correct_gcs_mNAVD':
      mapped_name = 'FEMAR2'
    elif self.grid == 'hsofs':
      mapped_name = 'HSOFS'

    return mapped_name

# -----------------------------------------------------------------------------
  def get_sequence_nr(self):
    if self.sequence_nr is None:
      return ''
    else:
      if self.asgs_instance is None:
        return ' (%s)' % self.sequence_nr
    return ' (%s)' % self.asgs_instance
#    return ' (%s)' % self.sequence_nr

# -----------------------------------------------------------------------------
  # windmodel for legend (difference maps - hindcast comparisons)
  def get_windmodel_diffmaps(self):
    if self.windmodel is not None:
      return '%s' % self.get_windmodel_display()

# -----------------------------------------------------------------------------
# adcrun_time in 'Time' select box (used in views.py)
  def get_adcrun_time(self):
    return self.adcrun_daytime_utc #.strftime('%H:%M %Z')

# -----------------------------------------------------------------------------
# calculate length of best track in days for hindcast track display in menu
  def get_hindcast_days(self):
    return (self.runend - self.runstart).days

# set data_host for pre-defined cache tiles
  def get_data_host_cache_display(self):
    data_host = self.wmsserver
    if data_host == 'NC1':
      return get_data_host_display('NC2')
    if data_host == 'NC2':
      return get_data_host_display('NC1')
    if data_host == 'LA5':
      return get_data_host_display('LA4')
    return get_data_host_display('LA5')
#    return get_data_host_display('LA4')


###############################################################################
class subtrack(models.Model):
  id = models.AutoField('ID', primary_key=True, unique=True)
  adcrunid = models.ForeignKey(adcrun_info, on_delete=models.CASCADE)
  trackid = models.ForeignKey(track, on_delete=models.CASCADE)

  def __unicode__(self):
    return "ID: %s" % (self.adcrunid.id)

#####################################################################################
LAYER_CHOICES = (
  ### timesteps layers SHP
  ("elevshp", "elevshp"),
  ("inunshp", "inunshp"),
  ("hsignshp", "hsignshp"),
  ("tpsshp", "tpsshp"),
  ("wvelshp", "wvelshp"),
  ("wvel10shp", "wvel10shp"),
  ### max layers SHP
  ("maxelevshp", "maxelevshp"),
  ("maxinunshp", "maxinunshp"),
  ("maxhsignshp", "maxhsignshp"),
  ("maxtpsshp", "maxtpsshp"),
  ("maxwvelshp", "maxwvelshp"),
  ("maxwvel10shp", "maxwvel10shp"),
  ### stations
  ("hydro", "hydro"),
  ("hydroval", "hydroval"),
  ("prec", "prec"),
  ("precimg", "precimg"),
  ### storm info
  ("track_invest", "track_invest"),
  ("track_sub", "track_sub"),
  ### timesteps layers TIF
  ("elev", "elev"),
  ("inun", "inun"),
  ("hsign", "hsign"),
  ("tps", "tps"),
  ("wvel", "wvel"),
  ("wvelf", "wvelf"),
  ### max layers TIF
  ("maxelev", "maxelev"),
  ("maxinun", "maxinun"),
  ("maxhsign", "maxhsign"),
  ("maxtps", "maxtps"),
  ("maxwvel", "maxwvel"),
  ### max layers (autoscale) TIF
  ("maxelev_auto", "maxelev_auto"),
  ("maxinun_auto", "maxinun_auto"),
  ("maxhsign_auto", "maxhsign_auto"),
  ("maxtps_auto", "maxtps_auto"),
  ("maxwvel_auto", "maxwvel_auto"),
  ### difference layers (hindcast comparisions)
  ("diffmaxwvelhist", "diffmaxwvelhist")
)

class layerinfo(models.Model):

  id = models.AutoField(primary_key=True, unique=True)
  layername = models.CharField('layer exists', max_length=20, choices = LAYER_CHOICES)
#  layer_output_start = models.DateTimeField('layer output start time', null=True, blank=True)
#  layer_output_end = models.DateTimeField('layer output end time', null=True, blank=True)
  show_layer = models.BooleanField(verbose_name='display layer', default=True)

  # this should be a many-to-many relation -> one layerinfo can have many adcrun_infos
  # adcrun_infos = models.ManyToManyField(adcrun_info)
  # the used approach blows up the DB but is much simpler in admin.py/views.py
  adcrun_info = models.ForeignKey(adcrun_info, on_delete=models.CASCADE)

  def __unicode__(self):
    return "%s" % self.adcrun_info

  class Meta:
    #name for class
    verbose_name_plural = "Layer Info"

################################################################################
# stations to display hydrographs
class hydro(models.Model):
  id = models.AutoField(primary_key=True, unique=True)
  stationid = models.CharField(max_length=18, null=True, blank=True)
  stationname = models.CharField(max_length=60, null=True, blank=True)
  state = models.CharField(max_length=2)
  agency = models.CharField(max_length=8)
  # human-readable for charts
  agencyname = models.CharField(max_length=8)
  realtimeurl = models.CharField(max_length=150, null=True, blank=True)
  alt_stationid = models.CharField(max_length=18, null=True, blank=True)
  alt_agencyname = models.CharField(max_length=8)
  alt_realtimeurl = models.CharField(max_length=150, null=True, blank=True)

  def __unicode__(self):
    return self.stationname

################################################################################
# stations to display precipitation
class prec(models.Model):
  id = models.AutoField(primary_key=True, unique=True)
  stationid = models.CharField(max_length=18, null=True, blank=True)
  stationname = models.CharField(max_length=60, null=True, blank=True)
  state = models.CharField(max_length=2)
  agency = models.CharField(max_length=9)
  agencyname = models.CharField(max_length=4)
  realtimeurl = models.CharField(max_length=150, null=True, blank=True)

  def __unicode__(self):
    return self.stationname

################################################################################
# assign CERA servers to HPC machines
# decides whether the complete CERA worklow (for nc_ng/pro) or the limited workflow (pub) will be executed on the given CERA server -> cera.process.py
class filter_ceraserver(models.Model):

  id = models.AutoField('ID', primary_key=True, unique=True)
  cera_datahost = models.CharField('CERA data host', max_length=4, null=True, blank=True, choices=WMSSERVER_CHOICES)
  adcirc_datahost = models.CharField('ADCIRC data host', max_length=30, null=True, blank=True, choices=ADCIRCDATAHOST_CHOICES)
  # combination CERA/ADCIRCHOST is allowed for ASGS runs
  active = models.BooleanField('active', default=False)
  # runs the pub or pro CERA workflow
  pro_model_run = models.BooleanField('PRO model run', help_text='Set to start the CERA workflow for the PRO website. If not set, the reduced workflow for the PUB website will be executed.', default=False)

  def __unicode__(self):
    return "%s" % self.id

  class Meta:
    verbose_name = "Filter CERA Servers"
    verbose_name_plural = "Filter CERA Servers"
    ordering = ['cera_datahost']

################################################################################
# filter ASGS runs (meshes and tracks) and assign default mesh
class filter_asgs(models.Model):

  #primary model run ID
  id = models.AutoField('ID', primary_key=True, unique=True)
  grid = models.CharField('ADCIRC grid', max_length=50, choices=GRID_CHOICES)

  # show this grid as default when multiple runs are available with the same starttime
  # will be used to set default grid for each run in adcrun_info with filldb_info.py
  default_view_ng = models.BooleanField('Default NG', default=False)
  default_view_nc = models.BooleanField('Default NC', default=False)
  default_view_pro = models.BooleanField('Default PRO', default=False)

  daily = models.BooleanField(default=True)
  stormt01 = models.BooleanField('NHC Consensus', default=True)
  stormt02 = models.BooleanField('max wind speed', default=True)
  stormt03 = models.BooleanField('over land speed', default=True)
  stormt04 = models.BooleanField('veer left', default=True)
  stormt05 = models.BooleanField('veer right', default=True)
  stormt06 = models.BooleanField('max radius', default=True)
  stormt07 = models.BooleanField('max wind speed only', default=True)
  stormt08 = models.BooleanField('constant max radius', default=True)
  stormt14 = models.BooleanField('shift left', default=True)
  stormt15 = models.BooleanField('shift right', default=True)
  # hypothetical runs
  stormt88 = models.BooleanField('synthetic', default=True)

  def __unicode__(self):
    return "%s" % self.id

  class Meta:
    verbose_name = "Filter ASGS Runs"
    verbose_name_plural = "Filter ASGS Runs"
    ordering = ['grid']

###############################################################################
def find_or_create_year(year):

    # try to find the year in 'storm_year'
    year_info = storm_year.objects.filter(year=year)

    if (len(year_info) == 0):
        # 'year' does not exist in db, create a new one
        thisyear = storm_year()
        thisyear.year = year
        thisyear.save(force_insert=True)

    else:
        # use existing record from 'storm_year' (entire data record)
        thisyear = year_info[0]

    return thisyear

def find_or_create_storminfo(this_year, stormnr, stormname, firstadv_dt, adv):

    storm_name = None
    if stormname is not None and len(stormname) > 0:
        storm_name = stormname

    has_hindcast = False
    if adv == '999':
        has_hindcast = True

    # try to find the storm via 'thisyear.id' and 'stormnr' in 'storm'
    storm_info = storm.objects \
                   .filter(year=this_year.id) \
                   .filter(storm_number=stormnr)

    if (len(storm_info) == 0):
        # 'storm' does not exist in db, create a new one
        thisstorm = storm()
        thisstorm.year = this_year
        thisstorm.storm_number = stormnr
        if storm_name is not None:
            thisstorm.stormname = storm_name
        else:
            thisstorm.stormname = "Storm: %s" % stormnr
        if firstadv_dt is not None:
            thisstorm.start_date_utc = firstadv_dt
        if has_hindcast:
            thisstorm.has_hindcast = True
        thisstorm.save(force_insert=True)

    else:
        # use existing record from db (entire data record)
        thisstorm = storm_info[0]

        # optional parameters may need to be upddated with each new run
        need_update = False
        if stormname is not None and thisstorm.stormname != stormname:
            thisstorm.stormname = stormname
            need_update = True
#        if len(firstadv) > 0 and thisstorm.start_date_utc != firstadv_dt:
        # firstadv in storm.bal is often too early and manually corrected in the DB, do not overwrite
        if firstadv_dt is not None and thisstorm.start_date_utc == None:
            thisstorm.start_date_utc = firstadv_dt
            need_update = True
        if has_hindcast and not thisstorm.has_hindcast:
            thisstorm.has_hindcast = True
            need_update = True
        if need_update:
            thisstorm.save(force_update=True)

    return thisstorm

def find_or_create_advinfo(this_storminfo, adv, stormclass, category, advtime_dt):

    # try to find the advisory via 'thisstorm.id' and 'adv' in 'advisory'
    adv_info = advisory.objects \
                 .filter(storm=this_storminfo.id) \
                 .filter(advisory=adv)

    if (len(adv_info) == 0):
        # 'advisory' does not exist in db, create a new one
        thisadv = advisory()
        thisadv.storm = this_storminfo
        thisadv.advisory = adv
        if stormclass is not None:
            thisadv.stormclass = stormclass
        if category is not None:
            thisadv.category = category
        if advtime_dt is not None:
            thisadv.adv_time_utc = advtime_dt
        thisadv.save(force_insert=True)

    else:
        # use existing record from db (entire data record)
        thisadv = adv_info[0]

        # optional parameters can be upddated with each new run
        need_update = False
        if stormclass is not None and thisadv.stormclass != stormclass:
            thisadv.stormclass = stormclass
            need_update = True
        if category is not None and thisadv.category != category:
            thisadv.category = category
            need_update = True
        if need_update:
            thisadv.save(force_update=True)

    return thisadv

def find_or_create_trackinfo(this_advinfo, tracknr, percent):

    if len(percent) == 0:
        percent = '0'

    # try to find the track via 'thisadv.id' and 'tracknr' in 'track'
    track_info = track.objects \
                   .filter(advisory=this_advinfo.id) \
                   .filter(track=tracknr) \
                   .filter(mod_percent=percent)

    if (len(track_info) == 0):
        # 'track' does not exist in db, create a new one
        thistrack = track()
        thistrack.advisory = this_advinfo
        thistrack.track = tracknr
        thistrack.mod_percent = percent
        thistrack.save(force_insert=True)

    else:
        # use existing record from 'track'
        thistrack = track_info[0]

    return thistrack

def create_storm_records(year, stormnr, stormname, firstadv_dt, adv, stormclass, category, advtime_dt, tracknr, percent):
    # the only unique storm model is the storm_year model
    # (given the available URL parameters)
    # thats why the test needs to start from the storm_year downwards

    this_year = find_or_create_year(year)
    this_storminfo = find_or_create_storminfo(this_year, stormnr, stormname, firstadv_dt, adv)
    this_advinfo = find_or_create_advinfo(this_storminfo, adv, stormclass, category, advtime_dt)
    this_track = find_or_create_trackinfo(this_advinfo, tracknr, percent)

    return this_track

##############################################################################
# signal handler will be called on new record/update of a record in
# model 'storm' (post_save) and changes the 'dependent_xxx' fields in the
# parent model 'year'
def on_storm_update(sender, **kwargs):

    changed_storm = kwargs.pop('instance', None)
    year = changed_storm.year

    if year is not None:
        year_storms = sender.objects.all().filter(year=year)

        # update the dependent_asgs_dev fields
        year.dependent_asgs_dev = False
        year.dependent_enable_public_dev = False
        year.dependent_enable_adminmode_dev = False

        storms_dev = year_storms.filter(dependent_asgs_dev=1)
        if storms_dev.count() > 0:
            year.dependent_asgs_dev = True
            if storms_dev.filter(dependent_enable_public_dev=1).count() > 0:
                year.dependent_enable_public_dev = True
            if storms_dev.filter(dependent_enable_adminmode_dev=1).count() > 0:
                year.dependent_enable_adminmode_dev = True

        # update the dependent_asgs_pro fields
        year.dependent_asgs_pro = False
        year.dependent_enable_public_pro = False
        year.dependent_enable_adminmode_pro = False

        storms_pro = year_storms.filter(dependent_asgs_pro=1)
        if storms_pro.count() > 0:
            year.dependent_asgs_pro = True
            if storms_pro.filter(dependent_enable_public_pro=1).count() > 0:
                year.dependent_enable_public_pro = True
            if storms_pro.filter(dependent_enable_adminmode_pro=1).count() > 0:
                year.dependent_enable_adminmode_pro = True

        # update the dependent_asgs_pub fields
        year.dependent_asgs_pub = False
        year.dependent_enable_public_pub = False
        year.dependent_enable_adminmode_pub = False

        storms_pub = year_storms.filter(dependent_asgs_pub=1)
        if storms_pub.count() > 0:
            year.dependent_asgs_pub = True
            if storms_pub.filter(dependent_enable_public_pub=1).count() > 0:
                year.dependent_enable_public_pub = True
            if storms_pub.filter(dependent_enable_adminmode_pub=1).count() > 0:
                year.dependent_enable_adminmode_pub = True

        # update the dependent_asgs_nc fields
        year.dependent_asgs_nc = False
        year.dependent_enable_public_nc = False
        year.dependent_enable_adminmode_nc = False

        storms_nc = year_storms.filter(dependent_asgs_nc=1)
        if storms_nc.count() > 0:
            year.dependent_asgs_nc = True
            if storms_nc.filter(dependent_enable_public_nc=1).count() > 0:
                year.dependent_enable_public_nc = True
            if storms_nc.filter(dependent_enable_adminmode_nc=1).count() > 0:
                year.dependent_enable_adminmode_nc = True

        # update the dependent_asgs_ng fields
        year.dependent_asgs_ng = False
        year.dependent_enable_public_ng = False
        year.dependent_enable_adminmode_ng = False

        storms_ng = year_storms.filter(dependent_asgs_ng=1)
        if storms_ng.count() > 0:
            year.dependent_asgs_ng = True
            if storms_ng.filter(dependent_enable_public_ng=1).count() > 0:
                year.dependent_enable_public_ng = True
            if storms_ng.filter(dependent_enable_adminmode_ng=1).count() > 0:
                year.dependent_enable_adminmode_ng = True

        # update the dependent_asgs_pr fields
        year.dependent_asgs_pr = False
        year.dependent_enable_public_pr = False
        year.dependent_enable_adminmode_pr = False

        storms_pr = year_storms.filter(dependent_asgs_pr=1)
        if storms_pr.count() > 0:
            year.dependent_asgs_pr = True
            if storms_pr.filter(dependent_enable_public_pr=1).count() > 0:
                year.dependent_enable_public_pr = True
            if storms_pr.filter(dependent_enable_adminmode_pr=1).count() > 0:
                year.dependent_enable_adminmode_pr = True

        # and update the dependent_asgs_ri fields
        year.dependent_asgs_ri = False
        year.dependent_enable_public_ri = False
        year.dependent_enable_adminmode_ri = False

        storms_ri = year_storms.filter(dependent_asgs_ri=1)
        if storms_ri.count() > 0:
            year.dependent_asgs_ri = True
            if storms_ri.filter(dependent_enable_public_ri=1).count() > 0:
                year.dependent_enable_public_ri = True
            if storms_ri.filter(dependent_enable_adminmode_ri=1).count() > 0:
                year.dependent_enable_adminmode_ri = True

        # update the dependent_asgs_st fields
        year.dependent_asgs_st = False
        year.dependent_enable_public_st = False
        year.dependent_enable_adminmode_st = False

        storms_st = year_storms.filter(dependent_asgs_st=1)
        if storms_st.count() > 0:
            year.dependent_asgs_st = True
            if storms_st.filter(dependent_enable_public_st=1).count() > 0:
                year.dependent_enable_public_st = True
            if storms_st.filter(dependent_enable_adminmode_st=1).count() > 0:
                year.dependent_enable_adminmode_st = True

        # update the dependent_region_nc_ng fields
        year.dependent_region_nc_ng = False

        storms_nc_ng = year_storms.filter(dependent_asgs_nc=1).filter(dependent_asgs_ng=1)
        if storms_st.count() > 0:
            year.dependent_asgs_st = True
            if storms_st.filter(dependent_enable_public_st=1).count() > 0:
                year.dependent_enable_public_st = True
            if storms_st.filter(dependent_enable_adminmode_st=1).count() > 0:
                year.dependent_enable_adminmode_st = True

        #####
        # dependent_region handling
        # dependent_region for pro is nc/ng/nc_ng; no region for dev/st/pub (always nc_ng)

        year.dependent_region_nc_ng = False
        storms_region_nc_ng = year_storms.filter(dependent_region_nc_ng = True)
        if storms_region_nc_ng.count() > 0:
            year.dependent_region_nc_ng = True

        year.dependent_region_nc = False
        storms_region_nc = year_storms.filter(dependent_region_nc = True)
        if storms_region_nc.count() > 0:
            year.dependent_region_nc = True

        year.dependent_region_ng = False
        storms_region_ng = year_storms.filter(dependent_region_ng = True)
        if storms_region_ng.count() > 0:
            year.dependent_region_ng = True

        year.dependent_region_pr = False
        storms_region_pr = year_storms.filter(dependent_region_pr = True)
        if storms_region_pr.count() > 0:
            year.dependent_region_pr = True

        year.dependent_region_ri = False
        storms_region_ri = year_storms.filter(dependent_region_ri = True)
        if storms_region_ri.count() > 0:
            year.dependent_region_ri = True

        year.save(force_update=True)

# register signal handlers for model 'storm'
post_save.connect(on_storm_update, sender=storm, dispatch_uid="storm1")
post_delete.connect(on_storm_update, sender=storm, dispatch_uid="storm2")


# signal handler will be called on new record/update of a record in
# model 'advisory' (post_save) and changes the 'dependent_xxx' fields in the
# parent model 'storm'
def on_advisory_update(sender, **kwargs):

    changed_advisory = kwargs.pop('instance', None)
    storm = changed_advisory.storm

    if storm is not None:
        storm_advs = sender.objects.all().filter(storm=storm)

        # update the dependent_asgs_dev fields
        storm.dependent_asgs_dev = False
        storm.dependent_enable_public_dev = False
        storm.dependent_enable_adminmode_dev = False

        advisories_dev = storm_advs.filter(dependent_asgs_dev=1)
        if advisories_dev.count() > 0:
            storm.dependent_asgs_dev = True
            if advisories_dev.filter(dependent_enable_public_dev=1).count() > 0:
                storm.dependent_enable_public_dev = True
            if advisories_dev.filter(dependent_enable_adminmode_dev=1).count() > 0:
                storm.dependent_enable_adminmode_dev = True

        # update the dependent_asgs_pro fields
        storm.dependent_asgs_pro = False
        storm.dependent_enable_public_pro = False
        storm.dependent_enable_adminmode_pro = False

        advisories_pro = storm_advs.filter(dependent_asgs_pro=1)
        if advisories_pro.count() > 0:
            storm.dependent_asgs_pro = True
            if advisories_pro.filter(dependent_enable_public_pro=1).count() > 0:
                storm.dependent_enable_public_pro = True
            if advisories_pro.filter(dependent_enable_adminmode_pro=1).count() > 0:
                storm.dependent_enable_adminmode_pro = True

	# update the dependent_asgs_pub fields
        storm.dependent_asgs_pub = False
        storm.dependent_enable_public_pub = False
        storm.dependent_enable_adminmode_pub = False

        advisories_pub = storm_advs.filter(dependent_asgs_pub=1)
        if advisories_pub.count() > 0:
            storm.dependent_asgs_pub = True
            if advisories_pub.filter(dependent_enable_public_pub=1).count() > 0:
                storm.dependent_enable_public_pub = True
            if advisories_pub.filter(dependent_enable_adminmode_pub=1).count() > 0:
                storm.dependent_enable_adminmode_pub = True

        # update the dependent_asgs_nc fields
        storm.dependent_asgs_nc = False
        storm.dependent_enable_public_nc = False
        storm.dependent_enable_adminmode_nc = False

        advisories_nc = storm_advs.filter(dependent_asgs_nc=1)

        if advisories_nc.count() > 0:
            storm.dependent_asgs_nc = True
            if advisories_nc.filter(dependent_enable_public_nc=1).count() > 0:
                storm.dependent_enable_public_nc = True
            if advisories_nc.filter(dependent_enable_adminmode_nc=1).count() > 0:
                storm.dependent_enable_adminmode_nc = True

        # update the dependent_asgs_ng fields
        storm.dependent_asgs_ng = False
        storm.dependent_enable_public_ng = False
        storm.dependent_enable_adminmode_ng = False

        advisories_ng = storm_advs.filter(dependent_asgs_ng=1)
        if advisories_ng.count() > 0:
            storm.dependent_asgs_ng = True
            if advisories_ng.filter(dependent_enable_public_ng=1).count() > 0:
                storm.dependent_enable_public_ng = True
            if advisories_ng.filter(dependent_enable_adminmode_ng=1).count() > 0:
                storm.dependent_enable_adminmode_ng = True

        # update the dependent_asgs_pr fields
        storm.dependent_asgs_pr = False
        storm.dependent_enable_public_pr = False
        storm.dependent_enable_adminmode_pr = False

        advisories_pr = storm_advs.filter(dependent_asgs_pr=1)
        if advisories_pr.count() > 0:
            storm.dependent_asgs_pr = True
            if advisories_pr.filter(dependent_enable_public_pr=1).count() > 0:
                storm.dependent_enable_public_pr = True
            if advisories_pr.filter(dependent_enable_adminmode_pr=1).count() > 0:
                storm.dependent_enable_adminmode_pr = True

        # update the dependent_asgs_ri fields
        storm.dependent_asgs_ri = False
        storm.dependent_enable_public_ri = False
        storm.dependent_enable_adminmode_ri = False

        advisories_ri = storm_advs.filter(dependent_asgs_ri=1)
        if advisories_ri.count() > 0:
            storm.dependent_asgs_ri = True
            if advisories_ri.filter(dependent_enable_public_ri=1).count() > 0:
                storm.dependent_enable_public_ri = True
            if advisories_ri.filter(dependent_enable_adminmode_ri=1).count() > 0:
                storm.dependent_enable_adminmode_ri = True

        # update the dependent_asgs_st fields
        storm.dependent_asgs_st = False
        storm.dependent_enable_public_st = False
        storm.dependent_enable_adminmode_st = False

        advisories_st = storm_advs.filter(dependent_asgs_st=1)
        if advisories_st.count() > 0:
            storm.dependent_asgs_st = True
            if advisories_st.filter(dependent_enable_public_st=1).count() > 0:
                storm.dependent_enable_public_st = True
            if advisories_st.filter(dependent_enable_adminmode_st=1).count() > 0:
                storm.dependent_enable_adminmode_st = True

        #####
        # dependent_region handling
        # dependent_region for pro is nc/ng/nc_ng; no region for dev/st/pub (always nc_ng)

        storm.dependent_region_nc_ng = False
        advisories_region_nc_ng = storm_advs.filter(dependent_region_nc_ng = True)
        if advisories_region_nc_ng.count() > 0:
            storm.dependent_region_nc_ng = True

        storm.dependent_region_nc = False
        advisories_region_nc = storm_advs.filter(dependent_region_nc = True)
        if advisories_region_nc.count() > 0:
            storm.dependent_region_nc = True

        storm.dependent_region_ng = False
        advisories_region_ng = storm_advs.filter(dependent_region_ng = True)
        if advisories_region_ng.count() > 0:
            storm.dependent_region_ng = True

        storm.dependent_region_pr = False
        advisories_region_pr = storm_advs.filter(dependent_region_pr = True)
        if advisories_region_pr.count() > 0:
            storm.dependent_region_pr = True

        storm.dependent_region_ri = False
        advisories_region_ri = storm_advs.filter(dependent_region_ri = True)
        if advisories_region_ri.count() > 0:
            storm.dependent_region_ri = True

        storm.save(force_update=True)

# register signal handlers for model 'advisory'
post_save.connect(on_advisory_update, sender=advisory, dispatch_uid="adv1")
post_delete.connect(on_advisory_update, sender=advisory, dispatch_uid="adv2")

# signal handler will be called on new record/update of a record in
# model 'track' (post_save) and changes the 'dependent_xxx' fields in the
# parent model 'advisory'
def on_track_update(sender, **kwargs):

    changed_track = kwargs.pop('instance', None)
    adv = changed_track.advisory

    # query for all tracks of the parent advisory
    if adv is not None:
        advisory_tracks = sender.objects.all().filter(advisory=adv)

        # update the dependent_asgs_dev fields
        adv.dependent_asgs_dev = False
        adv.dependent_enable_public_dev = False
        adv.dependent_enable_adminmode_dev = False

        tracks_dev = advisory_tracks.filter(dependent_asgs_dev=1)
        if tracks_dev.count() > 0:
            adv.dependent_asgs_dev = True
            if tracks_dev.filter(dependent_enable_public_dev=1).count() > 0:
                adv.dependent_enable_public_dev = True
            if tracks_dev.filter(dependent_enable_adminmode_dev=1).count() > 0:
                adv.dependent_enable_adminmode_dev = True

        # update the dependent_asgs_pro fields
        adv.dependent_asgs_pro = False
        adv.dependent_enable_public_pro = False
        adv.dependent_enable_adminmode_pro = False

        tracks_pro = advisory_tracks.filter(dependent_asgs_pro=1)
        if tracks_pro.count() > 0:
            adv.dependent_asgs_pro = True
            if tracks_pro.filter(dependent_enable_public_pro=1).count() > 0:
                adv.dependent_enable_public_pro = True
            if tracks_pro.filter(dependent_enable_adminmode_pro=1).count() > 0:
                adv.dependent_enable_adminmode_pro = True

        # update the dependent_asgs_pub fields
        adv.dependent_asgs_pub = False
        adv.dependent_enable_public_pub = False
        adv.dependent_enable_adminmode_pub = False

        tracks_pub = advisory_tracks.filter(dependent_asgs_pub=1)
        if tracks_pub.count() > 0:
            adv.dependent_asgs_pub = True
            if tracks_pub.filter(dependent_enable_public_pub=1).count() > 0:
                adv.dependent_enable_public_pub = True
            if tracks_pub.filter(dependent_enable_adminmode_pub=1).count() > 0:
                adv.dependent_enable_adminmode_pub = True

        # update the dependent_asgs_nc fields
        adv.dependent_asgs_nc = False
        adv.dependent_enable_public_nc = False
        adv.dependent_enable_adminmode_nc = False

        tracks_nc = advisory_tracks.filter(dependent_asgs_nc=1)
        if tracks_nc.count() > 0:
            adv.dependent_asgs_nc = True
            if tracks_nc.filter(dependent_enable_public_nc=1).count() > 0:
                adv.dependent_enable_public_nc = True
            if tracks_nc.filter(dependent_enable_adminmode_nc=1).count() > 0:
                adv.dependent_enable_adminmode_nc = True

        # update the dependent_asgs_ng fields
        adv.dependent_asgs_ng = False
        adv.dependent_enable_public_ng = False
        adv.dependent_enable_adminmode_ng = False

        tracks_ng = advisory_tracks.filter(dependent_asgs_ng=1)
        if tracks_ng.count() > 0:
            adv.dependent_asgs_ng = True
            if tracks_ng.filter(dependent_enable_public_ng=1).count() > 0:
                adv.dependent_enable_public_ng = True
            if tracks_ng.filter(dependent_enable_adminmode_ng=1).count() > 0:
                adv.dependent_enable_adminmode_ng = True

        # update the dependent_asgs_pr fields
        adv.dependent_asgs_pr = False
        adv.dependent_enable_public_pr = False
        adv.dependent_enable_adminmode_pr = False

        tracks_pr = advisory_tracks.filter(dependent_asgs_pr=1)
        if tracks_pr.count() > 0:
            adv.dependent_asgs_pr = True
            if tracks_pr.filter(dependent_enable_public_pr=1).count() > 0:
                adv.dependent_enable_public_pr = True
            if tracks_pr.filter(dependent_enable_adminmode_pr=1).count() > 0:
                adv.dependent_enable_adminmode_pr = True

        # update the dependent_asgs_ri fields
        adv.dependent_asgs_ri = False
        adv.dependent_enable_public_ri = False
        adv.dependent_enable_adminmode_ri = False

        tracks_ri = advisory_tracks.filter(dependent_asgs_ri=1)
        if tracks_ri.count() > 0:
            adv.dependent_asgs_ri = True
            if tracks_ri.filter(dependent_enable_public_ri=1).count() > 0:
                adv.dependent_enable_public_ri = True
            if tracks_ri.filter(dependent_enable_adminmode_ri=1).count() > 0:
                adv.dependent_enable_adminmode_ri = True

        # update the dependent_asgs_st fields
        adv.dependent_asgs_st = False
        adv.dependent_enable_public_st = False
        adv.dependent_enable_adminmode_st = False

        tracks_st = advisory_tracks.filter(dependent_asgs_st=1)
        if tracks_st.count() > 0:
            adv.dependent_asgs_st = True
            if tracks_st.filter(dependent_enable_public_st=1).count() > 0:
                adv.dependent_enable_public_st = True
            if tracks_st.filter(dependent_enable_adminmode_st=1).count() > 0:
                adv.dependent_enable_adminmode_st = True

        #####
        # dependent_region handling
        # dependent_region for pro is nc/ng/nc_ng; no region for dev/st/pub (always nc_ng)

        adv.dependent_region_nc_ng = False
        tracks_region_nc_ng = advisory_tracks.filter(dependent_region_nc_ng = True)
        if tracks_region_nc_ng.count() > 0:
            adv.dependent_region_nc_ng = True

        adv.dependent_region_nc = False
        tracks_region_nc = advisory_tracks.filter(dependent_region_nc = True)
        if tracks_region_nc.count() > 0:
            adv.dependent_region_nc = True

        adv.dependent_region_ng = False
        tracks_region_ng = advisory_tracks.filter(dependent_region_ng = True)
        if tracks_region_ng.count() > 0:
            adv.dependent_region_ng = True

        adv.dependent_region_pr = False
        tracks_region_pr = advisory_tracks.filter(dependent_region_pr = True)
        if tracks_region_pr.count() > 0:
            adv.dependent_region_pr = True

        adv.dependent_region_ri = False
        tracks_region_ri = advisory_tracks.filter(dependent_region_ri = True)
        if tracks_region_ri.count() > 0:
            adv.dependent_region_ri = True
        
        adv.has_model_run = True
        adv.save(force_update=True)

# register signal handlers for model 'track'
post_save.connect(on_track_update, sender=track, dispatch_uid="track1")
post_delete.connect(on_track_update, sender=track, dispatch_uid="track2")


# signal handler will be called on new record/update of a record in
# model 'adcrun_info' (post_save) and changes the 'dependent_xxx' fields
# in the model 'track'
def on_adcrun_info_update(sender, **kwargs):

    changed_adcruninfo = kwargs.pop('instance', None)
    trk = changed_adcruninfo.track_id

    # query for all infos of the parent track
    if trk is not None:
        track_adcrun_infos = sender.objects.all().filter(track_id=trk)

        # update the dependent_asgs_dev fields
        trk.dependent_asgs_dev = False
        trk.dependent_enable_public_dev = False
        trk.dependent_enable_adminmode_dev = False

        adcruns_dev = track_adcrun_infos.filter(asgs_dev=1)
        if adcruns_dev.count() > 0:
            trk.dependent_asgs_dev = True
            if adcruns_dev.filter(enable_public=1).count() > 0:
                trk.dependent_enable_public_dev = True
            if adcruns_dev.filter(enable_adminmode=1).count() > 0:
                trk.dependent_enable_adminmode_dev = True

        # update the dependent_asgs_pro fields
        trk.dependent_asgs_pro = False
        trk.dependent_enable_public_pro = False
        trk.dependent_enable_adminmode_pro = False

        adcruns_pro = track_adcrun_infos.filter(asgs_pro=1)
        if adcruns_pro.count() > 0:
            trk.dependent_asgs_pro = True
            if adcruns_pro.filter(enable_public=1).count() > 0:
                trk.dependent_enable_public_pro = True
            if adcruns_pro.filter(enable_adminmode=1).count() > 0:
                trk.dependent_enable_adminmode_pro = True

        # update the dependent_asgs_pub fields
        trk.dependent_asgs_pub = False
        trk.dependent_enable_public_pub = False
        trk.dependent_enable_adminmode_pub = False

        adcruns_pub = track_adcrun_infos.filter(asgs_pub=1)
        if adcruns_pub.count() > 0:
            trk.dependent_asgs_pub = True
            if adcruns_pub.filter(enable_public=1).count() > 0:
                trk.dependent_enable_public_pub = True
            if adcruns_pub.filter(enable_adminmode=1).count() > 0:
                trk.dependent_enable_adminmode_pub = True

        # update the dependent_asgs_nc fields
        trk.dependent_asgs_nc = False
        trk.dependent_enable_public_nc = False
        trk.dependent_enable_adminmode_nc = False

        adcruns_nc = track_adcrun_infos.filter(asgs_nc=1)
        if adcruns_nc.count() > 0:
            trk.dependent_asgs_nc = True
            if adcruns_nc.filter(enable_public=1).count() > 0:
                trk.dependent_enable_public_nc = True
            if adcruns_nc.filter(enable_adminmode=1).count() > 0:
                trk.dependent_enable_adminmode_nc = True

        # update the dependent_asgs_ng fields
        trk.dependent_asgs_ng = False
        trk.dependent_enable_public_ng = False
        trk.dependent_enable_adminmode_ng = False

        adcruns_ng = track_adcrun_infos.filter(asgs_ng=1)
        if adcruns_ng.count() > 0:
            trk.dependent_asgs_ng = True
            if adcruns_ng.filter(enable_public=1).count() > 0:
                trk.dependent_enable_public_ng = True
            if adcruns_ng.filter(enable_adminmode=1).count() > 0:
                trk.dependent_enable_adminmode_ng = True

        # update the dependent_asgs_pr fields
        trk.dependent_asgs_pr = False
        trk.dependent_enable_public_pr = False
        trk.dependent_enable_adminmode_pr = False

        adcruns_pr = track_adcrun_infos.filter(asgs_pr=1)
        if adcruns_pr.count() > 0:
            trk.dependent_asgs_pr = True
            if adcruns_pr.filter(enable_public=1).count() > 0:
                trk.dependent_enable_public_pr = True
            if adcruns_pr.filter(enable_adminmode=1).count() > 0:
                trk.dependent_enable_adminmode_pr = True

        # and update the dependent_asgs_ri of the parent track
        trk.dependent_asgs_ri = False
        trk.dependent_enable_public_ri = False
        trk.dependent_enable_adminmode_ri = False

        adcruns_ri = track_adcrun_infos.filter(asgs_ri=1)
        if adcruns_ri.count() > 0:
            trk.dependent_asgs_ri = True
            if adcruns_ri.filter(enable_public=1).count() > 0:
                trk.dependent_enable_public_ri = True
            if adcruns_ri.filter(enable_adminmode=1).count() > 0:
                trk.dependent_enable_adminmode_ri = True

        # and update the dependent_asgs_st of the parent track
        trk.dependent_asgs_st = False
        trk.dependent_enable_public_st = False
        trk.dependent_enable_adminmode_st = False

        adcruns_st = track_adcrun_infos.filter(asgs_st=1)
        if adcruns_st.count() > 0:
            trk.dependent_asgs_st = True
            if adcruns_st.filter(enable_public=1).count() > 0:
                trk.dependent_enable_public_st = True
            if adcruns_st.filter(enable_adminmode=1).count() > 0:
                trk.dependent_enable_adminmode_st = True

        #####
        # dependent_region handling
        # dependent_region for pro is nc/ng/nc_ng; no region for dev/st/pub (always nc_ng)

        trk.dependent_region_nc_ng = False
        adcruns_region_nc_ng = track_adcrun_infos.filter(website_region='nc_ng')
        if adcruns_region_nc_ng.count() > 0:
            trk.dependent_region_nc_ng = True

        trk.dependent_region_nc = False
        adcruns_region_nc = track_adcrun_infos.filter(website_region='nc')
        if adcruns_region_nc.count() > 0:
            trk.dependent_region_nc = True

        trk.dependent_region_ng = False
        adcruns_region_ng = track_adcrun_infos.filter(website_region='ng')
        if adcruns_region_ng.count() > 0:
            trk.dependent_region_ng = True

        trk.dependent_region_pr = False
        adcruns_region_pr = track_adcrun_infos.filter(website_region='pr')
        if adcruns_region_pr.count() > 0:
            trk.dependent_region_pr = True

        trk.dependent_region_ri = False
        adcruns_region_ri = track_adcrun_infos.filter(website_region='ri')
        if adcruns_region_ri.count() > 0:
            trk.dependent_region_ri = True
        
        trk.has_model_run = True
        trk.save(force_update=True)

##########################################################################
# This will be called before a record is saved to the database. It's used
# here to handle changed is_pseudo field values for the record being saved.
def on_adcrun_info_presave(sender, **kwargs):

    new_adcruninfo = kwargs.pop('instance', None)
    old_adcruninfo = sender.objects.all().filter(id=new_adcruninfo.id)

    if len(old_adcruninfo) == 0:
        return  # new record, nothing to do

    old_adcruninfo = old_adcruninfo[0]
    if old_adcruninfo.is_pseudo == new_adcruninfo.is_pseudo:
        return  # is_pseudo has not changed, nothing to do

    # dependent records for new adcinfo
    new_track = new_adcruninfo.track_id
    new_advisory = new_track.advisory
    new_storm = new_advisory.storm
    new_year = new_storm.year

    # handle case when record does not represent a pseudo storm anymore
    year = int(new_year.year)
    if old_adcruninfo.is_pseudo:
        if year >= 90000:
            year = year - 90000
        thistrack = create_storm_records(year, \
            new_storm.storm_number, new_storm.stormname, new_storm.start_date_utc, \
            new_advisory.advisory, new_advisory.stormclass, \
                new_advisory.category, new_advisory.adv_time_utc, \
            new_track.track, new_track.mod_percent)

    # handle case when record has now to represent a pseudo storm
    elif new_adcruninfo.is_pseudo:
        if year < 90000:
            year = year + 90000
        thistrack = create_storm_records(year, \
            new_storm.storm_number, new_storm.stormname, new_storm.start_date_utc, \
            new_advisory.advisory, new_advisory.stormclass, \
                new_advisory.category, new_advisory.adv_time_utc, \
            new_track.track, new_track.mod_percent)

    new_adcruninfo.track_id = thistrack

    return

###############################################################################
# register signal handlers
pre_save.connect(on_adcrun_info_presave, sender=adcrun_info, dispatch_uid="adcrun1")
post_save.connect(on_adcrun_info_update, sender=adcrun_info, dispatch_uid="adcrun2")
post_delete.connect(on_adcrun_info_update, sender=adcrun_info, dispatch_uid="adcrun3")
post_save.connect(create_profile, sender=User)

