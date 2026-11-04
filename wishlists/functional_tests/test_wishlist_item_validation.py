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

        titlebox = self.browser.find_element(By.ID, "id_title")
        titlebox.send_keys("Validation Wishlist")
        titlebox.send_keys(Keys.ENTER)

        list_url = self.browser.current_url

        # They try to submit an empty list item by hitting Enter on the empty input box
        self.get_item_input_box().send_keys(Keys.ENTER)

        # The page does not navigate away
        self.assertEqual(list_url, self.browser.current_url)

        # They enter a valid item
        self.get_item_input_box().send_keys("Christmas Item No.1")
        self.get_item_input_box().send_keys(Keys.ENTER)

        self.wait_for_row_in_list_table("Christmas Item No.1")

        # They accidentally try to enter a blank item into the current list
        self.get_item_input_box().send_keys(Keys.ENTER)

        # Again, the browser HTML5 validation marks the required field invalid
        self.wait_for_row_in_list_table("Christmas Item No.1")
        self.wait_for(lambda: self.browser.find_elements(By.CSS_SELECTOR, "#id_text:invalid"))

        # And they can correct it by filling some text in
        self.get_item_input_box().send_keys("Make tea")
        self.wait_for(lambda: self.browser.find_elements(By.CSS_SELECTOR, "#id_text:valid"))
        self.get_item_input_box().send_keys(Keys.ENTER)
        self.wait_for_row_in_list_table("Christmas Item No.1")
        self.wait_for_row_in_list_table("Make tea")
