# System
import uuid

# Django
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


class Wishlist(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False,
                            db_index=True, max_length=32)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return reverse('view_list', args=[self.uuid])


class Item(models.Model):
    text = models.TextField()
    wishlist = models.ForeignKey(Wishlist, default=None,
                                 on_delete=models.CASCADE)
