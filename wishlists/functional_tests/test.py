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

    def test_home_page(self):
        # The visiter visits the website url for the first time and notices the
        # the page title
        self.browser.get(self.live_server_url)
        self.assertIn('Welcome to the wishlists site', self.browser.title)

        # The visitor sees a text box that tells them to register or log in to
        # to view or create wishlists
        get_log_in_box = self.browser.find_element_by_id(
            'register_or_login').find_element_by_tag_name('p').text
        self.assertIn('Please register or login', get_log_in_box)

    def test_registration_on_home_page(self):
        # The visitor, clicks the register link is redirected to a page view
        # where they can register to join the website.
        self.browser.get(self.live_server_url)
        home_url = self.browser.current_url
        self.browser.find_element_by_link_text('Register').click()
        register_url = self.browser.current_url
        self.assertNotEqual(home_url, register_url)

        # The visitor sees a link to login with Facebook

        # The visitor sees a link to login with Twitter

        # The visitor sees a link to login with Google

        # The visitor sees a link to login with Microsoft
