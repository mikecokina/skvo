from observation.views import PhotometryListCreate, PhotometryMedia
from django.urls import path
from django.conf.urls import url

urlpatterns = [
    url(r'photometry/metadata/$', PhotometryListCreate.as_view(), name='metadata'),
    url(r'photometry/media/$', PhotometryMedia.as_view(), name='media'),
]
