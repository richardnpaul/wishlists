# Django
from django.test import TestCase

# Local
from ..forms import ItemForm, EMPTY_ITEM_ERROR
from ..models import Wishlist, Item


class ItemFormTest(TestCase):

    def test_form_renders_item_input_text(self):
        form = ItemForm()
        self.assertIn('placeholder="Enter a wishlist item here"', form.as_p())
        self.assertIn('class="form-control input-lg"', form.as_p())

    def test_form_validation_for_blank_items(self):
        form = ItemForm(data={'text': ''})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['text'],[EMPTY_ITEM_ERROR])

    def test_form_save_handles_saving_to_a_list(self):
        wishlist = Wishlist.objects.create()
        form = ItemForm(data={'text': 'do me'})
        new_item = form.save(for_list=wishlist)
        self.assertEqual(new_item, Item.objects.first())
        self.assertEqual(new_item.text, 'do me')
        self.assertEqual(new_item.wishlist, wishlist)