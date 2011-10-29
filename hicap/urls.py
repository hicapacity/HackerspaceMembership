from django.conf.urls.defaults import patterns, include, url
from hicap.membership.views import MemberView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', MemberView.frontpage, name='home'),
    url(r'^admin/', include(admin.site.urls)),
)
