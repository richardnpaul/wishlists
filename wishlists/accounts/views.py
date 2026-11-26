# Django Imports
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode, urlsafe_base64_encode

# Third-party Imports
from lists.forms import ItemForm

# Local
from .forms import LoginForm, RegistrationForm
from .tokens import account_activation_token


def safe_next(request, value, default="/"):
    """Return `value` if it's a safe same-site redirect target, else `default` (no open redirects)."""
    if value and url_has_allowed_host_and_scheme(
        value, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return value
    return default


def _requested_next(request):
    return safe_next(request, request.POST.get("next") or request.GET.get("next"), default="")


def account_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse("home_page"))


def account_login(request):
    if request.POST:
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            next_url = _requested_next(request) or "/"

            email = login_form.cleaned_data.get("email")
            password = login_form.cleaned_data.get("password")
            user = authenticate(request, username=email, password=password)

            if user is not None:
                if user.is_active:
                    login(
                        request,
                        user,
                        backend="django.contrib.auth.backends.ModelBackend",
                    )
                    return HttpResponseRedirect(next_url)
    else:
        login_form = LoginForm()
    return render(request, "login.html", {"login_form": login_form, "next": _requested_next(request)})


def account_registration(request):
    if request.POST:
        registration_form = RegistrationForm(request.POST)
        if registration_form.is_valid():
            user = registration_form.save(commit=False)
            user.is_active = False
            user.save()

            next_url = _requested_next(request)
            current_site = get_current_site(request)
            subject = f"Activate your {current_site.domain} account"
            message = render_to_string(
                "account_activation_email.html",
                {
                    "user": user,
                    "domain": current_site.domain,
                    "protocol": "https" if request.is_secure() else "http",
                    "next": next_url,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": account_activation_token.make_token(user),
                },
            )
            user.email_user(subject, message)

            check_mail_msg = f"""
            Please check your email account for your {current_site.domain}
            account confirmation email"""
            return render(
                request,
                "home.html",
                {
                    "messages": check_mail_msg,
                    "form": ItemForm(),
                    "login_form": LoginForm(),
                },
            )

    else:
        registration_form = RegistrationForm()
    return render(request, "register.html", {"form": registration_form, "next": _requested_next(request)})


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except TypeError, ValueError, OverflowError, User.DoesNotExist:
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        # Carries e.g. a group invite link through sign-up (see account_activation_email.html).
        return redirect(safe_next(request, request.GET.get("next"), default=reverse("home_page")))
    else:
        return render(request, "account_activation_invalid.html")
