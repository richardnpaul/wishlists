from django.contrib import admin
from .models import Wishlist, Item


class WishlistAdmin(admin.ModelAdmin):
    list_display = ['owner', 'title', 'uuid']


class ItemAdmin(admin.ModelAdmin):
    list_display = ['text', 'wishlist',]


admin.site.register(Wishlist, WishlistAdmin)
admin.site.register(Item, ItemAdmin)