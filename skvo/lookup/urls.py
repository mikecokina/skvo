from lookup.views import LookupPostView
from django.urls import path

urlpatterns = [
    path(r'search', LookupPostView.as_view(), name='search'),
]
