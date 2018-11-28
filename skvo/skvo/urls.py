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
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

# todo: add ping for opentsdb to avoid endless waiting


@api_view(['GET'])
def api_root(request, *args, **kwargs):
    return Response({
        'photometry-lookup': reverse('photometry-lookup-post', request=request),
        'photometry-access-reference': reverse('photometry-aref', request=request),
        'metadata': reverse('metadata', request=request),
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^api/$', api_root),
    url(r'^api/', include('lookup.urls')),
    url(r'^api/', include('observation.urls')),
]
