# Django
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# Local
from .models import Wishlist
from .forms import ItemForm
from accounts.forms import LoginForm


def home_page(request):
    return render(request, 'home.html', {
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
    return render(request, 'wishlist.html',
                  {'wishlist': wishlist, 'login_form': LoginForm()})

@login_required
def edit_list(request, wishlist_uuid):
    wishlist = Wishlist.objects.get(uuid=wishlist_uuid)
    form = ItemForm()
    if not request.user.is_authenticated:
        return redirect('/accounts/login/')
    if not wishlist.owner == request.user:
        return redirect('/accounts/login/')
    if request.POST:
        form = ItemForm(data=request.POST)
        if form.is_valid():
            form.save(for_list=wishlist, as_user=request.user)
            return redirect(wishlist)
    return render(request, 'edit_wishlist.html',
                  {'wishlist': wishlist, 'form': form,
                   'login_form': LoginForm()})
