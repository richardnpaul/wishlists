# Django
from django.shortcuts import render, redirect

# Local
from .models import Wishlist
from .forms import ItemForm
from accounts.forms import LoginForm


def home_page(request):
    return render(request, 'home.html', {
        'form': ItemForm(),
        'login_form': LoginForm()
    })


def new_list(request):
    form = ItemForm(data=request.POST)
    if form.is_valid():
        wishlist = Wishlist.objects.create()
        form.save(for_list=wishlist)
        return redirect(wishlist)
    else:
        return render(request, 'home.html', {'form': form})


def view_list(request, wishlist_uuid):
    wishlist = Wishlist.objects.get(uuid=wishlist_uuid)
    form = ItemForm()
    if request.POST:
        form = ItemForm(data=request.POST)
        if form.is_valid():
            form.save(for_list=wishlist)
            return redirect(wishlist)
    return render(request, 'wishlist.html',
                  {'wishlist': wishlist, 'form': form,
                   'login_form': LoginForm()})