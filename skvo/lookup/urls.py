from django.conf.urls import url
from django.urls import re_path

from lookup.views import PhotometryLookupPostView, PhotometryLookupGetView

urlpatterns = [
    url(r'^photometry/lookup/$', PhotometryLookupPostView.as_view(), name="photometry-lookup-post"),
    re_path(
        r'^photometry/lookup(?:/dataset/(?P<dataset>[0-9a-zA-Z]+))?'
        r'/ra/(?P<ra>[0-9]+\.?[0-9]*)'
        r'/de/(?P<de>[0-9]+\.?[0-9]*)'
        r'(?:/box_size_ra/(?P<box_size_ra>[0-9]+\.?[0-9]*))?'
        r'(?:/box_size_de/(?P<box_size_de>[0-9]+\.?[0-9]*))?'
        r'/$',
        PhotometryLookupGetView.as_view(), name="photometry-lookup-get-coo"),

    re_path(
        r'^photometry/lookup(?:/dataset/(?P<dataset>[0-9a-zA-Z]+))?'
        r'/target/(?P<target>[0-9a-zA-Z_\-]+)'
        r'(?:/box_size_ra/(?P<box_size_ra>[0-9]+\.?[0-9]*))?'
        r'(?:/box_size_de/(?P<box_size_de>[0-9]+\.?[0-9]*))?'
        r'/$',
        PhotometryLookupGetView.as_view(), name="photometry-lookup-get-target"),

    # re_path(r'^dataset/(?P<dataset>[0-9a-zA-Z]+)/target/(?P<target>[0-9a-zA-Z_\-]+)$',
    #         LookupGetView.as_view(), name="vo-search-target"),
]
