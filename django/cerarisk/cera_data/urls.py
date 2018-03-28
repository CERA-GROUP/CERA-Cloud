from django.conf.urls import include, url
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    url(r'^', include('cera_data.home.urls')),
    url(r'^adcircrun/', include('cera_data.adcircrun.urls')),
    url(r'^ceracgi/', include('cera_data.ceracgi.urls')),
    url(r'^accounts/', include('cera_data.accounts.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', admin.site.urls)
]

