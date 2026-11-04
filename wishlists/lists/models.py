# Standard Library Imports
import uuid

# Django Imports
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class Group(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False, db_index=True)
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(User, related_name="created_groups", on_delete=models.CASCADE)
    members = models.ManyToManyField(User, related_name="subscribed_groups", blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("group_detail", kwargs={"group_uuid": str(self.uuid)})

    def is_member(self, user):
        if not user.is_authenticated:
            return False
        return self.members.filter(pk=user.pk).exists()

    def is_creator(self, user):
        if not user.is_authenticated:
            return False
        return self.creator == user


class Wishlist(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False, db_index=True, max_length=32)
    owner = models.ForeignKey(User, related_name="wishlist_owner", on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    shared = models.ManyToManyField(User)
    is_private = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group, related_name="wishlists", blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    archived = models.BooleanField(default=False)

    class Meta:
        unique_together = ("owner", "title")

    def get_absolute_url(self):
        return reverse("view_list", args=[self.uuid])

    def can_view(self, user):
        if user.is_authenticated and user == self.owner:
            return True
        if not self.is_private:
            return True
        if user.is_authenticated and self.groups.filter(members=user).exists():
            return True
        return False

    @property
    def name(self):
        if self.title:
            return self.title
        else:
            return self.uuid


def can_view_wishlist(user, wishlist):
    return wishlist.can_view(user)


class Item(models.Model):
    PRIORITY_CHOICES = (
        ("1", "Highest"),
        ("2", "High"),
        ("3", "Medium"),
        ("4", "Low"),
        ("5", "Lowest"),
    )

    text = models.TextField()
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False, db_index=True, max_length=32)
    url = models.URLField(max_length=500, blank=True, default="")
    price = models.DecimalField(null=True, blank=True, decimal_places=2, max_digits=16)
    priority = models.CharField(default="3", choices=PRIORITY_CHOICES, max_length=1)
    notes = models.TextField(null=True, blank=True)
    wishlist = models.ForeignKey(Wishlist, default=None, on_delete=models.CASCADE)
    gifter = models.ForeignKey(User, default=None, null=True, blank=True, on_delete=models.SET_DEFAULT)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    archived = models.BooleanField(default=False)
    ordered = models.BooleanField(default=False)
    delivered = models.BooleanField(default=False)
    wrapped = models.BooleanField(default=False)

    class Meta:
        ordering = ("priority", "wishlist", "id")
        constraints = [
            models.UniqueConstraint(fields=["text", "wishlist", "uuid"], name="Unique wishlist items"),
        ]

    def get_absolute_url(self):
        return reverse("view_list_item", args=[self.uuid])

    @property
    def wishlist_owner(self):
        return self.wishlist.owner

    @property
    def wishlist_title(self):
        return self.wishlist.title
