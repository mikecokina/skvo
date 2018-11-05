from lookup.views import LookupPostView
from django.urls import path

urlpatterns = [
    path(r'lookup', LookupPostView.as_view(), name='search'),
]
