from django.conf.urls import url
from django.conf import settings
from cera_data.home import views

urlpatterns = [
    url(r'^$', views.cera_home, name='home'),
]

