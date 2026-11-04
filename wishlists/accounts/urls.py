# Django Imports
from django.contrib.auth import views as auth_views
from django.urls import include, path, reverse_lazy

# Local
from . import views


urlpatterns = [
    path("login/", views.account_login, name="account_login"),
    path("logout/", views.account_logout, name="account_logout"),
    path("register/", views.account_registration, name="account_registration"),
    path("activate/<str:uidb64>/<str:token>/", views.activate, name="activate"),
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
            success_url=reverse_lazy("password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<str:uidb64>/<str:token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url=reverse_lazy("password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    path("", include("social_django.urls", namespace="social")),
]
