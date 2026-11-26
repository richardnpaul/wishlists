# Django Imports
from django.urls import path

# Local
from . import views


urlpatterns = [
    path("", views.group_list, name="group_list"),
    path("create/", views.group_create, name="group_create"),
    path("<uuid:group_uuid>/", views.group_detail, name="group_detail"),
    path("<uuid:group_uuid>/subscribe/", views.group_subscribe, name="group_subscribe"),
    path("<uuid:group_uuid>/unsubscribe/", views.group_unsubscribe, name="group_unsubscribe"),
]
