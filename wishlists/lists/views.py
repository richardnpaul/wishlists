# Django
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# Local
from .models import Wishlist
from .forms import ItemForm
from accounts.forms import LoginForm


def home_page(request):
    return render(request, 'home.html', {
        'form': ItemForm(),
        'login_form': LoginForm()
    })

@login_required
def new_list(request):
    form = ItemForm(data=request.POST)
    if form.is_valid():
        wishlist = Wishlist.objects.create(owner=request.user)
        form.save(for_list=wishlist, as_user=request.user)
        return redirect(wishlist)
    else:
        return render(request, 'home.html', {'form': form})


def view_list(request, wishlist_uuid):
    wishlist = Wishlist.objects.get(uuid=wishlist_uuid)
    form = ItemForm()
    if request.POST:
        if not request.user.is_authenticated:
            return redirect('/accounts/login/')
        form = ItemForm(data=request.POST)
        if form.is_valid():
            if request.user == wishlist.owner:
                form.save(for_list=wishlist, as_user=request.user)
                return redirect(wishlist)
            else:
                redirect(wishlist)
    return render(request, 'wishlist.html',
                  {'wishlist': wishlist, 'form': form,
                   'login_form': LoginForm()})