# System
import uuid

# Django
from django.db import models


class Wishlist(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False,
                            db_index=True, max_length=32)


class Item(models.Model):
    text = models.TextField()
    wishlist = models.ForeignKey(Wishlist, default=None,
                                 on_delete=models.CASCADE)
