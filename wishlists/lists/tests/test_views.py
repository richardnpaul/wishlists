# Django
from django.test import TestCase
from django.utils.html import escape

# Local
from ..models import Item, Wishlist
from ..forms import ItemForm, EMPTY_ITEM_ERROR


class HomePageTest(TestCase):

    def test_uses_home_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'home.html')

    def test_home_page_uses_itemform(self):
        response = self.client.get('/')
        self.assertIsInstance(response.context['form'], ItemForm)


class NewListTest(TestCase):

    def test_can_save_post_request(self):
        self.client.post('/wishlists/new/',
                         data={'text': 'Item for List no.1'})
        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, 'Item for List no.1')

    def test_redirects_after_post(self):
        response = self.client.post('/wishlists/new/',
                        data={'text': 'Item for List no.1'})
        new_wishlist = Wishlist.objects.first()
        self.assertRedirects(response, f'/wishlists/{new_wishlist.uuid}/')

    def test_for_invalid_input_renders_home_template(self):
        response = self.client.post('/wishlists/new/', data={'text': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')


    def test_validation_errors_are_shown_on_home_page(self):
        response = self.client.post('/wishlists/new/', data={'text': ''})
        self.assertContains(response, escape(EMPTY_ITEM_ERROR))


    def test_for_invalid_input_passes_form_to_template(self):
        response = self.client.post('/wishlists/new/', data={'text': ''})
        self.assertIsInstance(response.context['form'], ItemForm)


    def test_invalid_list_items_arent_saved(self):
        self.client.post('/wishlists/new/', data={'text': ''})
        self.assertEqual(Wishlist.objects.count(), 0)
        self.assertEqual(Item.objects.count(), 0)


class ListViewTest(TestCase):

    def test_displays_only_items_for_that_list(self):
        correct_wishlist = Wishlist.objects.create()
        Item.objects.create(text='Christmas wish no.1',
                                    wishlist=correct_wishlist)
        Item.objects.create(text='Christmas wish no.2',
                                    wishlist=correct_wishlist)

        other_wishlist = Wishlist.objects.create()
        Item.objects.create(text='Other Christmas wishlist item no.1',
                            wishlist=other_wishlist)
        Item.objects.create(text='Other Christmas wishlist item no.2',
                            wishlist=other_wishlist)

        response = self.client.get(f'/wishlists/{correct_wishlist.uuid}/')

        self.assertContains(response, 'Christmas wish no.1')
        self.assertContains(response, 'Christmas wish no.2')
        self.assertNotContains(response, 'Other Christmas wishlist item no.1')
        self.assertNotContains(response, 'Other Christmas wishlist item no.2')

    def test_uses_wishlist_template(self):
        wishlist = Wishlist.objects.create()
        response = self.client.get(f'/wishlists/{wishlist.uuid}/')
        self.assertTemplateUsed(response, 'wishlist.html')

    def test_passes_correct_wishlist_to_template(self):
        other_wishlist = Wishlist.objects.create()
        correct_wishlist = Wishlist.objects.create()
        response = self.client.get(f'/wishlists/{correct_wishlist.uuid}/')
        self.assertEqual(response.context['wishlist'], correct_wishlist)

    def test_displays_item_form(self):
        wishlist = Wishlist.objects.create()
        response = self.client.get(f'/wishlists/{wishlist.uuid}/')
        self.assertIsInstance(response.context['form'], ItemForm)
        self.assertContains(response, 'name="text"')

    def test_can_save_a_post_request_to_an_existing_wishlist(self):
        other_wishlist = Wishlist.objects.create()
        correct_wishlist = Wishlist.objects.create()
        self.client.post(
            f'/wishlists/{correct_wishlist.uuid}/',
            data={'text': 'New item for existing wishlist'}
        )

        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, 'New item for existing wishlist')
        self.assertEqual(new_item.wishlist, correct_wishlist)

