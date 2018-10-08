# System
import uuid

# Django
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


class Wishlist(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False,
                            db_index=True, max_length=32)
    owner = models.ForeignKey(User, related_name='wishlist_owner',
                              on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    shared = models.ManyToManyField(User)

    class Meta:
        unique_together = ('owner', 'title',)

    def get_absolute_url(self):
        return reverse('view_list', args=[self.uuid])

    @property
    def name(self):
        if self.title:
            return self.title
        else:
            return self.uuid


class Item(models.Model):
    text = models.TextField()
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False,
                            db_index=True, max_length=32)
    wishlist = models.ForeignKey(Wishlist, default=None,
                                 on_delete=models.CASCADE)
    gifter = models.ForeignKey(User, default=None, null=True,
                               on_delete=models.SET_DEFAULT)

    class Meta:
        ordering = ('wishlist','id',)
        unique_together = ('text', 'wishlist',)

    def get_absolute_url(self):
        return reverse('view_list_item', args=[self.uuid])
