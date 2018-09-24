# Django
from django.urls import path, include

# Local
from . import views

urlpatterns = [
    path('login/', views.account_login, name='account_login'),
    path('logout/', views.account_logout, name='account_logout'),
    path('register/', views.account_registration, name='account_registration'),
    path('activate/<str:uidb64>/<str:token>/', views.activate, name='activate'),
    path('', include('social_django.urls', namespace='social'))
]