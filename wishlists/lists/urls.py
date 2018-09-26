from django.urls import path

from . import views

urlpatterns = [
    path('new/', views.new_list, name='new_list'),
    path('<uuid:wishlist_uuid>/', views.view_list, name='view_list'),
    path('<uuid:wishlist_uuid>/edit/', views.edit_list, name='edit_list'),
]