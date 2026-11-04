# Django Imports
from django.contrib.auth.models import User
from django.test import TestCase

# Local
from ..forms import EMPTY_ITEM_ERROR, ItemForm, WishListForm
from ..models import Item, Wishlist


class ItemFormTest(TestCase):
    def test_form_renders_item_input_text(self):
        form = ItemForm()
        self.assertIn('placeholder="Enter a wishlist item here"', form.as_p())
        self.assertIn('class="form-control"', form.as_p())

    def test_form_validation_for_blank_items(self):
        form = ItemForm(data={"text": ""})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["text"], [EMPTY_ITEM_ERROR])

    def test_form_save_handles_saving_to_a_list(self):
        user = User.objects.create_user(username="testuser", password="password")
        wishlist = Wishlist.objects.create(owner=user, title="Test Wishlist")
        form = ItemForm(data={"text": "do me"})
        self.assertTrue(form.is_valid())
        new_item = form.save(for_list=wishlist, as_user=user)
        self.assertEqual(new_item, Item.objects.first())
        self.assertEqual(new_item.text, "do me")
        self.assertEqual(new_item.wishlist, wishlist)


class WishListFormTest(TestCase):
    def test_form_renders_title_input(self):
        form = WishListForm()
        self.assertIn('placeholder="Enter a title for your wishlist here"', form.as_p())

    def test_form_validation_for_blank_title(self):
        form = WishListForm(data={"title": ""})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["title"], ["You can't have an empty wishlist title"])

    def test_form_save(self):
        user = User.objects.create_user(username="testuser2", password="password")
        form = WishListForm(data={"title": "Birthday Wishes"})
        self.assertTrue(form.is_valid())
        wishlist = form.save(as_user=user)
        self.assertEqual(wishlist.title, "Birthday Wishes")
        self.assertEqual(wishlist.owner, user)
