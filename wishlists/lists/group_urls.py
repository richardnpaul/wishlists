# Django Imports
from django.urls import path

# Local
from . import views


urlpatterns = [
    path("", views.group_list, name="group_list"),
    path("create/", views.group_create, name="group_create"),
    path("join/<str:token>/", views.group_join, name="group_join"),
    path("<uuid:group_uuid>/", views.group_detail, name="group_detail"),
    path("<uuid:group_uuid>/leave/", views.group_leave, name="group_leave"),
    path("<uuid:group_uuid>/edit/", views.group_edit, name="group_edit"),
    path("<uuid:group_uuid>/delete/", views.group_delete, name="group_delete"),
    path("<uuid:group_uuid>/invite/reset/", views.group_reset_invite, name="group_reset_invite"),
    path(
        "<uuid:group_uuid>/members/<int:user_id>/remove/",
        views.group_remove_member,
        name="group_remove_member",
    ),
]
