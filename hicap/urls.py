from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # url(r'^$', 'hicap.views.home', name='home'),
    # url(r'^hicap/', include('hicap.foo.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
