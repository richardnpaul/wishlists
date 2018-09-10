# Django
from django.shortcuts import render, redirect

# Local
from .models import Item, Wishlist


def home_page(request):
    return render(request, 'home.html')


def view_list(request, wishlist_id):
    wishlist = Wishlist.objects.get(id=wishlist_id)
    return render(request, 'wishlist.html', {'wishlist': wishlist})


def new_list(request):
    wishlist = Wishlist.objects.create()
    Item.objects.create(text=request.POST['item_text'], wishlist=wishlist)
    return redirect(f'/wishlists/{wishlist.id}/')


def add_item(request, wishlist_id):
    wishlist = Wishlist.objects.get(id=wishlist_id)
    Item.objects.create(text=request.POST['item_text'], wishlist=wishlist)
    return redirect(f'/wishlists/{wishlist.id}/')
