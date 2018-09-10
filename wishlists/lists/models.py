# Django
from django.db import models


class Wishlist(models.Model):
    pass


class Item(models.Model):
    text = models.TextField()
    wishlist = models.ForeignKey(Wishlist, default=None,
                                 on_delete=models.CASCADE)
