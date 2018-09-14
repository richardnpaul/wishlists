# Django
from django.urls import path

# Local
from . import views

urlpatterns = [
    path('login/', views.account_login, name='account_login'),
    # path('register/', views.account_registration, name='account_registration'),
    # path('<uuid:wishlist_uuid>/', views.view_list, name='view_list'),
]