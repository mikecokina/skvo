"""skvo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import include
from django.conf.urls import url
from django.contrib import admin
from django.urls import path
from django.urls import re_path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from lookup.views import LookupGetView

# todo: add ping for opentsdb to avoid endless waiting


@api_view(['GET'])
def api_root(request, *args, **kwargs):
    return Response({
        'lookup': reverse('lookup', request=request),
        'metadata': reverse('metadata', request=request),
    })


urlpatterns = [
    re_path(r'^dataset/(?P<dataset>[0-9a-zA-Z]+)/ra/(?P<ra>[0-9]+\.?[0-9]*)/de/(?P<de>[0-9]+\.?[0-9]*)$',
            LookupGetView.as_view(), name="vo-search-no-target"),

    re_path(r'^dataset/(?P<dataset>[0-9a-zA-Z]+)/target/(?P<target>[0-9a-zA-Z_\-]+)$',
            LookupGetView.as_view(), name="vo-search-target"),

    path('admin/', admin.site.urls),
    url(r'^api/$', api_root),
    url(r'^api/', include('lookup.urls')),
    url(r'^api/', include('observation.urls')),
]
