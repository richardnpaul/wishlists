# Django
from django.test import TestCase

# Local
from ..models import Item


class HomePageTest(TestCase):

    def test_home_page_view_renders_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'home.html')

    def test_accepts_POST_request_on_item_submission(self):
        response = self.client.post('/',
                                    data={'item_text': 'Christmas wish no.1'})

        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, 'Christmas wish no.1')

    def test_redirects_after_post(self):
        response = self.client.post('/',
                                    data={'item_text': 'Christmas wish no.1'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/wishlists/just-the-one-list/')

    def test_home_page_displays_all_created_items(self):
        item1 = Item.objects.create(text='Christmas wish no.1')
        item2 = Item.objects.create(text='Christmas wish no.2')
        response = self.client.get('/')
        self.assertContains(response, 'Christmas wish no.1')
        self.assertContains(response, 'Christmas wish no.2')

    def test_only_save_items_when_necessary(self):
        self.client.get('/')
        self.assertEqual(Item.objects.count(), 0)

