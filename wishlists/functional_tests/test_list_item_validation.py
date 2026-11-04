# Third-party Imports
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Local
from .base import FunctionalTest


class NewVisitorTest(FunctionalTest):
    def test_can_start_a_list_for_one_user(self):
        # A user logs in and visits the website
        self.create_pre_authenticated_session(username="visitor1@example.com")
        self.browser.get(self.live_server_url)
        self.assertIn("Welcome to the wishlists site", self.browser.title)

        # The visitor sees an input field on the home page to start a new wishlist
        titlebox = self.browser.find_element(By.ID, "id_title")
        self.assertEqual("Enter a title for your wishlist here", titlebox.get_attribute("placeholder"))
        titlebox.send_keys("Christmas Wishlist")
        titlebox.send_keys(Keys.ENTER)

        # The visitor is redirected to the edit page where an item input box appears
        inputbox = self.get_item_input_box()
        self.assertEqual("Enter a wishlist item here", inputbox.get_attribute("placeholder"))

        # They type in a desired item.
        inputbox.send_keys("Christmas wish no.1")
        inputbox.send_keys(Keys.ENTER)

        # On pressing enter, the item is added to the page and a new empty input box appears
        self.wait_for_row_in_list_table("Christmas wish no.1")
        inputbox = self.get_item_input_box()
        self.assertEqual("Enter a wishlist item here", inputbox.get_attribute("placeholder"))

        # So the visitor adds another item
        inputbox.send_keys("Christmas wish no.2")
        inputbox.send_keys(Keys.ENTER)
        self.wait_for_row_in_list_table("Christmas wish no.1")
        self.wait_for_row_in_list_table("Christmas wish no.2")

    def test_multiple_users_can_start_lists_at_different_urls(self):
        # User 1 starts a new list
        self.create_pre_authenticated_session(username="alice@example.com")
        self.browser.get(self.live_server_url)

        titlebox = self.browser.find_element(By.ID, "id_title")
        titlebox.send_keys("Alice Wishlist")
        titlebox.send_keys(Keys.ENTER)

        inputbox = self.get_item_input_box()
        inputbox.send_keys("First list item")
        inputbox.send_keys(Keys.ENTER)

        self.wait_for_row_in_list_table("First list item")

        # The site generates a unique url on post submission which can be visited to see the list
        v1_url = self.browser.current_url
        self.assertRegex(v1_url, r"/wishlists/.+/")

        # Shut down browser and start a new session to clear out v1's stuff
        self.browser.quit()
        self.browser = self.create_browser()

        # A new visitor (User 2) comes along and logs in
        self.create_pre_authenticated_session(username="bob@example.com")
        self.browser.get(self.live_server_url)
        page_text = self.browser.find_element(By.TAG_NAME, "body").text
        self.assertNotIn("First list item", page_text)

        titlebox = self.browser.find_element(By.ID, "id_title")
        titlebox.send_keys("Bob Wishlist")
        titlebox.send_keys(Keys.ENTER)

        inputbox = self.get_item_input_box()
        inputbox.send_keys("v2's first item")
        inputbox.send_keys(Keys.ENTER)

        self.wait_for_row_in_list_table("v2's first item")
        v2_url = self.browser.current_url

        self.assertRegex(v2_url, r"/wishlists/.+/")
        self.assertNotEqual(v1_url, v2_url)

        new_page_text = self.browser.find_element(By.TAG_NAME, "body").text
        self.assertNotIn("First list item", new_page_text)
