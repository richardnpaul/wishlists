# Django Imports
from django.contrib import admin

from .models import Group, Item, Wishlist


class GroupAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "creator", "uuid", "created", "modified"]
    list_filter = ["created", "modified"]
    search_fields = ["name", "creator__username", "creator__email"]
    filter_horizontal = ["members"]
    readonly_fields = ["uuid", "created", "modified"]


class WishlistAdmin(admin.ModelAdmin):
    list_display = ["id", "owner", "title", "uuid", "is_private", "get_groups", "created"]
    list_filter = ["is_private", "groups", "created"]
    search_fields = ["title", "owner__username", "owner__email"]
    filter_horizontal = ["groups"]
    readonly_fields = ["uuid", "created", "modified"]

    @admin.display(description="Groups")
    def get_groups(self, obj):
        return ", ".join([g.name for g in obj.groups.all()])


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


admin.site.register(Group, GroupAdmin)
admin.site.register(Wishlist, WishlistAdmin)
admin.site.register(Item, ItemAdmin)
