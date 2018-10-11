from datapipe.views import Upload
from django.urls import path

urlpatterns = [
    path(r'upload', Upload.as_view(), name='upload'),
]
