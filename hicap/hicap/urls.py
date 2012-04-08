from django.conf.urls.defaults import patterns, include, url
from hicap.membership.views import MemberView, admin_member_report

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
		url(r'^$', MemberView.frontpage, name='home'),
		url(r'^maker/login/$', MemberView.login, name='maker_login'),
		url(r'^maker/panel/$', MemberView.panel, name='maker_panel'),
		url(r'^admin/membership/report/', admin_member_report),
		url(r'^admin/', include(admin.site.urls)),
		url(r'^admin_tools/', include('admin_tools.urls')),
    url(r'^_paypal_ipn/', include('paypal.standard.ipn.urls')),
)
