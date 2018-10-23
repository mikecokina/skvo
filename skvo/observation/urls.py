from observation.views import PhotometryList
from django.urls import path

urlpatterns = [
    path(r'metadata', PhotometryList.as_view(), name='metadata'),
]
