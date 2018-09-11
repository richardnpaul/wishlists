# System
import uuid

# Django
from django.db import models
from django.urls import reverse


class Wishlist(models.Model):
    # name = models.CharField(default=None)
    # private = models.BooleanField(default=True)
    # owner = models.OneToOneField()
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False,
                            db_index=True, max_length=32)

    def get_absolute_url(self):
        return reverse('view_list', args=[self.uuid])


class Item(models.Model):
    PRIORITY_CHOICES = (
        ('highest', 'Highest'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
        ('lowest', 'Lowest'),
    )

    text = models.TextField()
    url = models.URLField()
    price = models.DecimalField(null=True, blank=True, decimal_places=2,
                                max_digits=16)
    number = models.IntegerField(default=1)
    priority = models.CharField(default='medium', choices=PRIORITY_CHOICES,
                                max_length=8)
    # notes = models.TextField()
    # date_added = models.DateTimeField()
    wishlist = models.ForeignKey(Wishlist, default=None,
                                 on_delete=models.CASCADE)
