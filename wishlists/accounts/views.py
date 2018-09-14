# Django
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth import login, authenticate

# Local
from .forms import LoginForm

def account_login(request):
    if request.POST:
        form = LoginForm(request.POST)
        if form.is_valid():
            next_url = request.GET.get('next', '/')

            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponseRedirect(next_url)
            else:
                return HttpResponseForbidden()
    else:
        return HttpResponseForbidden()