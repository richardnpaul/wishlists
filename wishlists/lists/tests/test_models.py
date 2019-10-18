# Django
from django.test import TestCase
from django.core.exceptions import ValidationError

# Local
from ..models import Item, Wishlist


class ListAndItemModelTest(TestCase):
    def test_saving_and_retrieving_items(self):
        wishlist = Wishlist()
        wishlist.save()

        first_item = Item()
        first_item.text = "The first ever item"
        first_item.wishlist = wishlist
        first_item.save()

        second_item = Item()
        second_item.text = "The second item"
        second_item.wishlist = wishlist
        second_item.save()

        saved_wishlist = Wishlist.objects.first()
        self.assertEqual(saved_wishlist, wishlist)

        saved_items = Item.objects.all()
        self.assertEqual(saved_items.count(), 2)

        first_saved_item = saved_items[0]
        second_saved_item = saved_items[1]
        self.assertEqual(first_saved_item.text, "The first ever item")
        self.assertEqual(first_saved_item.wishlist, wishlist)
        self.assertEqual(second_saved_item.text, "The second item")
        self.assertEqual(second_saved_item.wishlist, wishlist)

    def test_cannot_save_empty_list_items(self):
        wishlist = Wishlist.objects.create()
        item = Item(wishlist=wishlist, text="")
        with self.assertRaises(ValidationError):
            item.save()
            item.full_clean()

    def test_get_absolute_url(self):
        wishlist = Wishlist.objects.create()
        self.assertEqual(wishlist.get_absolute_url(), f"/wishlists/{wishlist.uuid}/")
