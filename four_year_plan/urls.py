from django.conf.urls import include, url

from django.contrib import admin

from planner.views import home

admin.autodiscover()

urlpatterns = [#'',# is '' OK?

    url(r'^$', home, name='home'), # is this right?
    url(r'^planner/', include('planner.urls')),

    url(r'^accounts/', include('django.contrib.auth.urls')),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', admin.site.urls),
]
