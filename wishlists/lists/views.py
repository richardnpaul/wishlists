# Django
from django.shortcuts import render, redirect

# Local
from .models import Item, Wishlist


def home_page(request):
    return render(request, 'home.html')


def view_list(request, wishlist_uuid):
    wishlist = Wishlist.objects.get(uuid=wishlist_uuid)
    return render(request, 'wishlist.html', {'wishlist': wishlist})


def new_list(request):
    wishlist = Wishlist.objects.create()
    Item.objects.create(text=request.POST['item_text'], wishlist=wishlist)
    return redirect(f'/wishlists/{wishlist.uuid}/')


def add_item(request, wishlist_uuid):
    wishlist = Wishlist.objects.get(uuid=wishlist_uuid)
    Item.objects.create(text=request.POST['item_text'], wishlist=wishlist)
    return redirect(f'/wishlists/{wishlist.uuid}/')
