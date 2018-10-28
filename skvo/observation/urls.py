from observation.views import PhotometryList, PhotometryMedia
from django.urls import path

urlpatterns = [
    path(r'photometry/metadata', PhotometryList.as_view(), name='metadata'),
    path(r'photometry/media', PhotometryMedia.as_view(), name='media'),
]
