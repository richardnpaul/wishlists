# Django
from django.test import TestCase

# Local
from ..models import Item, Wishlist


class HomePageTest(TestCase):

    def test_home_page_view_renders_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'home.html')

    def test_only_save_items_when_necessary(self):
        self.client.get('/')
        self.assertEqual(Item.objects.count(), 0)


class ListViewTest(TestCase):

    def test_home_page_displays_all_created_items(self):
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

    def test_uses_template(self):
        wishlist = Wishlist.objects.create()
        response = self.client.get(f'/wishlists/{wishlist.uuid}/')
        self.assertTemplateUsed(response, 'wishlist.html')


class NewListTest(TestCase):

    def test_can_save_post_request(self):
        self.client.post('/wishlists/new/',
                         data={'item_text': 'Item for List no.1'})
        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, 'Item for List no.1')

    def test_redirects_after_post(self):
        response = self.client.post('/wishlists/new/',
                        data={'item_text': 'Item for List no.1'})
        new_wishlist = Wishlist.objects.first()
        self.assertRedirects(response, f'/wishlists/{new_wishlist.uuid}/')

    def test_can_save_a_post_request_to_an_existing_list(self):
        other_wishlist = Wishlist.objects.create()
        correct_wishlist = Wishlist.objects.create()

        self.client.post(
            f'/wishlists/{correct_wishlist.uuid}/add_item/',
            data={'item_text': 'New item for an existing wishlist'}
        )

        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(Wishlist.objects.count(), 2)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, 'New item for an existing wishlist')
        self.assertEqual(new_item.wishlist, correct_wishlist)

    def test_redirects_to_list_view(self):
        other_wishlist = Wishlist.objects.create()
        correct_wishlist = Wishlist.objects.create()

        response = self.client.post(
            f'/wishlists/{correct_wishlist.uuid}/add_item/',
            data={'item_text': 'New item for an existing wishlist'}
        )

        self.assertRedirects(response, f'/wishlists/{correct_wishlist.uuid}/')

    def test_passes_correct_list_to_template(self):
        other_wishlist = Wishlist.objects.create()
        correct_wishlist = Wishlist.objects.create()
        response = self.client.get(f'/wishlists/{correct_wishlist.uuid}/')
        self.assertEqual(response.context['wishlist'], correct_wishlist)
