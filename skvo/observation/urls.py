from observation.views import PhotometryList, PhotometryMedia
from django.urls import path
from django.conf.urls import url

urlpatterns = [
    url(r'photometry/metadata/$', PhotometryList.as_view(), name='metadata'),
    url(r'photometry/media/$', PhotometryMedia.as_view(), name='media'),
]
