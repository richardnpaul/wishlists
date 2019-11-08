# System
import uuid

# Django
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


class Wishlist(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False, db_index=True, max_length=32)
    owner = models.ForeignKey(User, related_name="wishlist_owner", on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    shared = models.ManyToManyField(User)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    archived = models.BooleanField(default=False)

    class Meta:
        unique_together = ("owner", "title")

    def get_absolute_url(self):
        return reverse("view_list", args=[self.uuid])

    @property
    def name(self):
        if self.title:
            return self.title
        else:
            return self.uuid


class Item(models.Model):

    PRIORITY_CHOICES = (("1", "Highest"), ("2", "High"), ("3", "Medium"), ("4", "Low"), ("5", "Lowest"))

    text = models.TextField()
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False, db_index=True, max_length=32)
    url = models.URLField(max_length=500, blank=True, default="")
    price = models.DecimalField(null=True, blank=True, decimal_places=2, max_digits=16)
    priority = models.CharField(default="medium", choices=PRIORITY_CHOICES, max_length=1)
    notes = models.TextField(null=True, blank=True)
    wishlist = models.ForeignKey(Wishlist, default=None, on_delete=models.CASCADE)
    gifter = models.ForeignKey(User, default=None, null=True, on_delete=models.SET_DEFAULT)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    archived = models.BooleanField(default=False)
    ordered = models.BooleanField(default=False)
    delivered = models.BooleanField(default=False)
    wrapped = models.BooleanField(default=False)

    class Meta:
        ordering = ("priority", "wishlist", "id")
        unique_together = ("text", "wishlist")

    def get_absolute_url(self):
        return reverse("view_list_item", args=[self.uuid])
