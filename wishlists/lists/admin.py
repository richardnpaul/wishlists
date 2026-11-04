# Django Imports
from django.contrib import admin

from .models import Item, Wishlist


class WishlistAdmin(admin.ModelAdmin):
    list_display = ["id", "owner", "title", "uuid", "created"]


class ItemAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "wishlist_owner",
        "wishlist_title",
        "text",
        "wishlist",
        "created",
        "modified",
    ]


admin.site.register(Wishlist, WishlistAdmin)
admin.site.register(Item, ItemAdmin)
