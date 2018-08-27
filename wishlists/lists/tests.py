# Django
from django.test import TestCase
from django.http import HttpRequest

# Local
from .views import home_page


class HomePageTest(TestCase):

    def test_home_page_view_renders_template(self):
        request = HttpRequest()
        response = home_page(request)
        self.assertTemplateUsed(response, 'home.html')
