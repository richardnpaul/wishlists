# Standard Library Imports

# Django Imports
from django.contrib.auth import get_user_model

# Third-party Imports
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Local
from functional_tests.base import FunctionalTest
from lists.models import Wishlist


User = get_user_model()


def _get_group_model():
    from lists.models import Group

    return Group


class GroupsAndWishlistPrivacyFunctionalTest(FunctionalTest):
    """End-to-end Selenium browser tests for Groups, Wishlist Privacy, and Access Control."""

    def setUp(self):
        super().setUp()
        self.alice = User.objects.create_user(
            username="alice@example.com",
            email="alice@example.com",
            password="alicepassword123!",
        )
        self.bob = User.objects.create_user(
            username="bob@example.com",
            email="bob@example.com",
            password="bobpassword123!",
        )
        self.charlie = User.objects.create_user(
            username="charlie@example.com",
            email="charlie@example.com",
            password="charliepassword123!",
        )

    def test_group_discovery_creation_and_subscription_flow(self):
        """User journey: Alice creates a group; Bob discovers it and subscribes."""
        # 1. Alice logs in
        self.create_pre_authenticated_session(username="alice@example.com", password="alicepassword123!")

        # 2. Alice clicks on the Groups navbar link
        self.browser.get(self.live_server_url)
        groups_link = self.wait_for(lambda: self.browser.find_element(By.LINK_TEXT, "Groups"))
        groups_link.click()

        # Alice arrives at /groups/
        self.wait_for(lambda: self.assertIn("/groups/", self.browser.current_url))

        # Alice clicks Create Group
        create_btn = self.wait_for(
            lambda: self.browser.find_element(
                By.XPATH,
                "//a[contains(@href, '/groups/create/') or contains(text(), 'Create Group')]",
            )
        )
        create_btn.click()

        # 3. Alice fills out the group creation form
        name_input = self.wait_for(lambda: self.browser.find_element(By.NAME, "name"))
        desc_input = self.browser.find_element(By.NAME, "description")

        name_input.send_keys("Board Game Guild")
        desc_input.send_keys("Tabletop gaming and strategy board games.")
        submit_btn = self.browser.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
        submit_btn.click()

        # Alice sees the newly created group listed
        self.wait_for(lambda: self.assertIn("Board Game Guild", self.browser.find_element(By.TAG_NAME, "body").text))

        # 4. Bob logs in in a fresh browser session
        self.browser.quit()
        self.browser = self.create_browser()
        self.create_pre_authenticated_session(username="bob@example.com", password="bobpassword123!")

        # Bob visits /groups/
        self.browser.get(self.live_server_url + "/groups/")
        self.wait_for(lambda: self.assertIn("Board Game Guild", self.browser.find_element(By.TAG_NAME, "body").text))

        # Bob subscribes to the group
        subscribe_btn = self.wait_for(
            lambda: self.browser.find_element(
                By.XPATH,
                "//button[contains(text(), 'Subscribe')]"
                " | //input[@value='Subscribe']"
                " | //a[contains(@href, 'subscribe')]",
            )
        )
        subscribe_btn.click()

        # Bob's status reflects subscription
        Group = _get_group_model()
        group = Group.objects.get(name="Board Game Guild")
        self.wait_for(lambda: self.assertTrue(group.members.filter(id=self.bob.id).exists()))

    def test_wishlist_privacy_default_and_group_exposure_access_flow(self):
        """User journey: Alice creates private wishlist.

        Bob (non-member) cannot view it. Alice shares it with Board Game Guild.
        Bob (member) can now view it. Charlie (non-member) cannot. Alice makes
        it public, and Charlie can view it.
        """
        Group = _get_group_model()
        group = Group.objects.create(creator=self.alice, name="Board Game Guild")
        group.members.add(self.alice, self.bob)

        # 1. Alice creates a new wishlist
        self.create_pre_authenticated_session(username="alice@example.com", password="alicepassword123!")
        self.browser.get(self.live_server_url)

        titlebox = self.get_title_input_box()
        titlebox.send_keys("Alice Secret Gaming List")
        titlebox.send_keys(Keys.ENTER)

        # Alice adds an item
        inputbox = self.get_item_input_box()
        inputbox.send_keys("Catan 3D Collector Edition")
        inputbox.send_keys(Keys.ENTER)
        self.wait_for_row_in_list_table("Catan 3D Collector Edition")

        # Verify wishlist defaulted to private in database
        alice_wishlist = Wishlist.objects.get(title="Alice Secret Gaming List", owner=self.alice)
        self.assertTrue(
            alice_wishlist.is_private,
            "CRITICAL REQUIREMENT: Wishlists must default to private upon creation.",
        )
        wishlist_url = self.live_server_url + f"/wishlists/{alice_wishlist.uuid}/"

        # 2. Bob logs in and tries to access Alice's unexposed private wishlist
        self.browser.quit()
        self.browser = self.create_browser()
        self.create_pre_authenticated_session(username="bob@example.com", password="bobpassword123!")
        self.browser.get(wishlist_url)

        # Bob should receive a 403 Forbidden or Permission Denied error
        body_text = self.wait_for(lambda: self.browser.find_element(By.TAG_NAME, "body").text)
        self.assertTrue(
            "403" in body_text or "Permission Denied" in body_text or "Forbidden" in body_text,
            f"Non-member Bob should be denied access to private unshared wishlist. Got page: {body_text[:100]}",
        )

        # 3. Alice exposes the wishlist to Board Game Guild
        alice_wishlist.groups.add(group)

        # 4. Bob visits the wishlist again — now accessible because Bob is in Board Game Guild!
        self.browser.get(wishlist_url)
        self.wait_for_row_in_list_table("Catan 3D Collector Edition")

        # 5. Charlie (who is NOT in Board Game Guild) tries to access the wishlist
        self.browser.quit()
        self.browser = self.create_browser()
        self.create_pre_authenticated_session(username="charlie@example.com", password="charliepassword123!")
        self.browser.get(wishlist_url)

        # Charlie should be denied access
        body_text = self.wait_for(lambda: self.browser.find_element(By.TAG_NAME, "body").text)
        self.assertTrue(
            "403" in body_text or "Permission Denied" in body_text or "Forbidden" in body_text,
            "Outsider Charlie should be denied access to group-private wishlist.",
        )

        # 6. Alice toggles the wishlist to public
        alice_wishlist.is_private = False
        alice_wishlist.save()

        # 7. Charlie visits again — now accessible because it's public!
        self.browser.get(wishlist_url)
        self.wait_for_row_in_list_table("Catan 3D Collector Edition")

    def test_navbar_groups_link_visibility(self):
        """Navbar displays 'Groups' link when logged in; hides when anonymous."""
        # Anonymous visits home page
        self.browser.get(self.live_server_url)
        nav_text = self.browser.find_element(By.TAG_NAME, "nav").text
        self.assertNotIn("Groups", nav_text)

        # User logs in
        self.create_pre_authenticated_session(username="alice@example.com", password="alicepassword123!")
        self.browser.get(self.live_server_url)
        groups_link = self.wait_for(lambda: self.browser.find_element(By.LINK_TEXT, "Groups"))
        self.assertTrue(groups_link.is_displayed())
