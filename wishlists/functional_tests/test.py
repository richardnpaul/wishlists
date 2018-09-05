# System packages
import time

# Django includes
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

# 3rd party packages
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException

MAX_WAIT = 5


def wait(fn):
    def modified_fn(*args, **kwargs):
        start_time = time.time()
        while True:
            try:
                return fn(*args, **kwargs)
            except (AssertionError, WebDriverException) as e:
                if time.time() - start_time > MAX_WAIT:
                    raise e
                time.sleep(0.5)
    return modified_fn


class FunctionalTest(StaticLiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    @wait
    def wait_for(self, fn):
        return fn()

    @wait
    def wait_for_row_in_list_table(self, row_text):
        table = self.browser.find_element_by_tag_name('table')
        rows = table.find_elements_by_tag_name('tr')
        self.assertIn(row_text, [row.text for row in rows])

    def get_item_input_box(self):
        return self.browser.find_element_by_tag_name('input')

    def test_home_page(self):
        # The visiter visits the website url for the first time and notices the
        # the page title
        self.browser.get(self.live_server_url)
        self.assertIn('Welcome to the wishlists site', self.browser.title)

        # Next, the visitor sees an input field into which they can enter text
        # The placeholder text tells them to enter a wishlist item
        inputbox = self.get_item_input_box()
        self.assertEqual(
            'Enter a wishlist item here',
            inputbox.get_attribute('placeholder')
        )

        # They type in a desired item.
        inputbox.send_keys('Christmas wish no.1')

        # On pressing enter, the item is added to the page and a new empty
        # input box appears
        inputbox.send_keys(Keys.ENTER)
        self.assertEqual(
            'Enter a wishlist item here',
            inputbox.get_attribute('placeholder')
        )
        self.wait_for_row_in_list_table('Christmas wish no.1')

        # So the visitor adds another item
        inputbox.send_keys('Christmas wish no.2')
        inputbox.send_keys(Keys.ENTER)
        self.wait_for_row_in_list_table('Christmas wish no.1')
        self.wait_for_row_in_list_table('Christmas wish no.2')
