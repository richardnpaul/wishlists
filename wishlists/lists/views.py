# Django
from django.shortcuts import render, redirect

# Local
from .models import Item


def home_page(request):
    if request.method == 'POST':
        Item.objects.create(text=request.POST['item_text'])
        return redirect('/')
    item_list = Item.objects.all()
    return render(request, 'home.html', {'items': item_list})

