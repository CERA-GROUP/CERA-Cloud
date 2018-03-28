from django.conf.urls import url
#from django.conf import settings
from cera_data.accounts import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^login/$', auth_views.login, {'template_name': 'accounts/login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, {'template_name': 'accounts/logout.html'}, name='logout'),

    url(r'^signup/$', views.signup, name='signup'),
    url(r'^contact/$', views.contact, name='contact'),
    # for signup + contact
    url(r'^contact_done/$', views.contact_done, name='contact_done'),

    url(r'^password_reset/$', auth_views.password_reset, {'template_name': 'accounts/password_reset.html'}, name='password_reset'),
    url(r'^password_reset_done/$', auth_views.password_reset_done, {'template_name': 'accounts/password_reset_done.html'}, name='password_reset_done'),
    url(r'^password_reset_confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', auth_views.password_reset_confirm, name='password_reset_confirm'),
    url(r'^password_reset_complete/$', auth_views.password_reset_complete, {'template_name': 'accounts/password_reset_complete.html'}, name='password_reset_complete'),

    url(r'^password_change/$', views.password_change, name='password_change'),
    url(r'^password_change_done/$', auth_views.password_change_done, {'template_name': 'accounts/password_change_done.html'}, name='password_change_done'),

    url(r'^profile/$', views.profile, name='profile'),
    url(r'^profile_edit/$', views.profile_edit, name='profile_edit')

]

