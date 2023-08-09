from django.conf.urls import include, url
from django.urls import path

from django.contrib import admin

from planner.views import department_load_summary

admin.autodiscover()

urlpatterns = [#'',# is '' OK?

    url(r'^$', department_load_summary, name='department_load_summary'),
    url(r'^planner/', include('planner.urls')),

    url(r'^accounts/', include('django.contrib.auth.urls')),
    #url(r'^accounts/login/', include('django.contrib.auth.urls')),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', admin.site.urls),
]

# the following is to allow login/logout from the browsable api
urlpatterns += [
    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),
]
