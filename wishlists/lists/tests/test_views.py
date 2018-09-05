# Django
from django.test import TestCase

# Local
from ..models import Item


class HomePageTest(TestCase):

    def test_home_page_view_renders_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'home.html')

    def test_home_page_accepts_POST_request_on_item_submission(self):
        response = self.client.post('/', data={'item_text': 'Christmas wish no.1'})
        self.assertIn('Christmas wish no.1', response.content.decode())
        self.assertTemplateUsed(response, 'home.html')

    def test_home_page_displays_all_created_items(self):
        item1 = Item.objects.create(text='Christmas wish no.1')
        item2 = Item.objects.create(text='Christmas wish no.2')
        response = self.client.get('/')
        self.assertContains(response, 'Christmas wish no.1')
        self.assertContains(response, 'Christmas wish no.2')
