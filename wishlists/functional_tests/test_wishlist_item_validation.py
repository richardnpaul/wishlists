# Third-party Imports
from selenium.webdriver.common.keys import Keys

# Local
from .base import FunctionalTest


class ItemValidationTest(FunctionalTest):
    def test_cannot_add_empty_list_items(self):
        # A visitor goes to the home page and tries to submit
        # an empty list item. They hit the Enter key on the empty input box
        self.browser.get(self.live_server_url)
        home_url = self.browser.current_url
        self.get_item_input_box().send_keys(Keys.ENTER)

        self.assertEqual(home_url, self.browser.current_url)

        self.get_item_input_box().send_keys("Christmas Item No.1")
        self.get_item_input_box().send_keys(Keys.ENTER)

        self.wait_for_row_in_list_table("Christmas Item No.1")
        new_list_url = self.browser.current_url
        self.assertNotEqual(home_url, new_list_url)

        # They accidentally try to enter a blank item into a current list
        self.get_item_input_box().send_keys(Keys.ENTER)

        # Again, the browser will not comply
        self.wait_for_row_in_list_table("Christmas Item No.1")
        self.wait_for(lambda: self.browser.find_elements_by_css_selector("#id_text:invalid"))

        # And she can correct it by filling some text in
        self.get_item_input_box().send_keys("Make tea")
        self.wait_for(lambda: self.browser.find_elements_by_css_selector("#id_text:valid"))
        self.get_item_input_box().send_keys(Keys.ENTER)
        self.wait_for_row_in_list_table("1: Buy milk")
        self.wait_for_row_in_list_table("2: Make tea")
