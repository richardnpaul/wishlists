# System packages
import time

# Django includes
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

# 3rd party packages
from selenium import webdriver


class FunctionalTest(StaticLiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    def test_home_page_loads(self):
        # Visiter visits the website url for the first time and notices the
        # the page title
        self.browser.get('http://localhost:8000')
        self.assertIn('Welcome to the wishlists site', self.browser.title)

