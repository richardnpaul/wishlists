# Django Imports
from django.contrib import admin

from .models import Item, Wishlist, Gifter


class WishlistAdmin(admin.ModelAdmin):
    list_display = ["owner", "title", "uuid"]


class ItemAdmin(admin.ModelAdmin):
    list_display = ["text", "wishlist"]


class GifterAdmin(admin.ModelAdmin):
    list_display = ["gifter", "item", "quantity"]


admin.site.register(Wishlist, WishlistAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(Gifter, GifterAdmin)
