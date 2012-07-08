from django.conf.urls.defaults import patterns, include, url
from hicap.membership.views import MemberView, admin_member_report, admin_member_report_ajax, admin_payment_report_ajax

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
		url(r'^$', MemberView.frontpage, name='home'),
		url(r'^maker/login/$', MemberView.login, name='maker_login'),
		url(r'^maker/logout/$', MemberView.logout, name='maker_logout'),
		url(r'^maker/panel/$', MemberView.panel, name='maker_panel'),
		url(r'^maker/info/$', MemberView.info, name='maker_info'),
		url(r'^maker/profile/$', MemberView.profile, name='maker_profile'),
		url(r'^maker/password/$', MemberView.password, name='maker_password'),
		url(r'^maker/password_reset/$', MemberView.password_reset, name='maker_password_reset'),
		url(r'^maker/password_reset_request/$', MemberView.password_reset_request, name='maker_password_reset_request'),
		url(r'^maker/billing/$', MemberView.billing, name='maker_billing'),
		url(r'^maker/community/$', MemberView.community, name='maker_community'),
		url(r'^admin/membership/report/', admin_member_report),
		url(r'^admin/membership/report_ajax/', admin_member_report_ajax),
		url(r'^admin/payment/report_ajax/', admin_payment_report_ajax),
		url(r'^admin/', include(admin.site.urls)),
		url(r'^admin_tools/', include('admin_tools.urls')),
    url(r'^_paypal_ipn/', include('paypal.standard.ipn.urls')),
)
