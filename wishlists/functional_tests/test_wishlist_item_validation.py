# Third-party Imports
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Local
from .base import FunctionalTest


class ItemValidationTest(FunctionalTest):
    def test_cannot_add_empty_list_items(self):
        # A visitor logs in, visits the home page, and creates a wishlist
        self.create_pre_authenticated_session(username="validator@example.com")
        self.browser.get(self.live_server_url)

        titlebox = self.get_title_input_box()
        titlebox.send_keys("Validation Wishlist")
        titlebox.send_keys(Keys.ENTER)

        # Wait for the item input box on the edit page
        inputbox = self.get_item_input_box()
        list_url = self.browser.current_url

        # They try to submit an empty list item by hitting Enter on the empty input box
        inputbox.send_keys(Keys.ENTER)

        # HTML5 validation marks the required field invalid and prevents navigation
        self.wait_for(lambda: self.browser.find_element(By.CSS_SELECTOR, "#id_text:invalid"))
        self.assertEqual(list_url, self.browser.current_url)

        # They enter a valid item
        inputbox = self.get_item_input_box()
        inputbox.send_keys("Christmas Item No.1")
        inputbox.send_keys(Keys.ENTER)

        self.wait_for_row_in_list_table("Christmas Item No.1")

        # They accidentally try to enter a blank item into the current list
        inputbox = self.get_item_input_box()
        inputbox.send_keys(Keys.ENTER)

        # Again, the browser HTML5 validation marks the required field invalid
        self.wait_for_row_in_list_table("Christmas Item No.1")
        self.wait_for(lambda: self.browser.find_element(By.CSS_SELECTOR, "#id_text:invalid"))

        # And they can correct it by filling some text in
        inputbox = self.get_item_input_box()
        inputbox.send_keys("Make tea")
        self.wait_for(lambda: self.browser.find_element(By.CSS_SELECTOR, "#id_text:valid"))
        inputbox.send_keys(Keys.ENTER)
        self.wait_for_row_in_list_table("Christmas Item No.1")
        self.wait_for_row_in_list_table("Make tea")
