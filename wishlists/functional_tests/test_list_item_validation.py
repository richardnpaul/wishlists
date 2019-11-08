# 3rd party packages
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

# Local
from .base import FunctionalTest


class NewVisitorTest(FunctionalTest):
    def test_can_start_a_list_for_one_user(self):
        # The visiter visits the website url for the first time and notices the
        # the page title
        self.browser.get(self.live_server_url)
        self.assertIn("Welcome to the wishlists site", self.browser.title)

        # Next, the visitor sees an input field into which they can enter text
        # The placeholder text tells them to enter a wishlist item
        inputbox = self.get_item_input_box()
        self.assertEqual("Enter a wishlist item here", inputbox.get_attribute("placeholder"))

        # They type in a desired item.
        inputbox.send_keys("Christmas wish no.1")

        # On pressing enter, the item is added to the page and a new empty
        # input box appears
        inputbox.send_keys(Keys.ENTER)
        self.assertEqual("Enter a wishlist item here", inputbox.get_attribute("placeholder"))
        self.wait_for_row_in_list_table("Christmas wish no.1")

        inputbox = self.get_item_input_box()
        # So the visitor adds another item
        inputbox.send_keys("Christmas wish no.2")
        inputbox.send_keys(Keys.ENTER)
        self.wait_for_row_in_list_table("Christmas wish no.1")
        self.wait_for_row_in_list_table("Christmas wish no.2")

    def test_multiple_users_can_start_lists_at_different_urls(self):
        # Visitor starts a new list
        self.browser.get(self.live_server_url)

        inputbox = self.get_item_input_box()
        inputbox.send_keys("First list item")
        inputbox.send_keys(Keys.ENTER)

        self.wait_for_row_in_list_table("First list item")

        # The visitor wonders if the site saves multiple lists, the site
        # generates a unique url on post submission which can be visited to see
        # the list
        v1_url = self.browser.current_url
        self.assertRegex(v1_url, "/wishlists/.+/")

        # Shut down browser and start a new session to clear out v1's stuff
        self.browser.quit()
        self.browser = webdriver.Firefox()

        # A new visitor comes along and starts a list
        self.browser.get(self.live_server_url)
        page_text = self.browser.find_element_by_tag_name("body").text
        self.assertNotIn("First list item", page_text)

        inputbox = self.get_item_input_box()
        inputbox.send_keys("v2's first item")
        inputbox.send_keys(Keys.ENTER)

        self.wait_for_row_in_list_table("v2's first item")
        v2_url = self.browser.current_url

        self.assertRegex(v2_url, "/wishlists/.+/")
        self.assertNotEqual(v1_url, v2_url)

        new_page_text = self.browser.find_element_by_tag_name("body").text
        self.assertNotIn("First list item", new_page_text)
