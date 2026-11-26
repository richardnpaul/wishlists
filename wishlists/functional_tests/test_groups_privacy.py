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

    def body_text(self):
        return self.browser.find_element(By.TAG_NAME, "body").text

    def test_group_invite_link_join_and_shared_list_flow(self):
        """User journey: Alice creates a group and a list, shares the list with the group and sends Bob
        the invite link; Bob joins and finds the list under "Shared with me"."""
        # 1. Alice logs in and creates a group from the Groups page.
        self.create_pre_authenticated_session(username="alice@example.com", password="alicepassword123!")
        self.browser.get(self.live_server_url)
        self.wait_for(lambda: self.browser.find_element(By.LINK_TEXT, "Groups")).click()
        self.wait_for(lambda: self.browser.find_element(By.LINK_TEXT, "Create New Group")).click()

        self.wait_for(lambda: self.browser.find_element(By.NAME, "name")).send_keys("Board Game Guild")
        self.browser.find_element(By.NAME, "description").send_keys("Tabletop gaming and strategy board games.")
        self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # She lands on the group page, which shows her an invite link.
        invite_input = self.wait_for(lambda: self.browser.find_element(By.ID, "invite_url"))
        invite_url = invite_input.get_attribute("value")
        self.assertIn("/groups/join/", invite_url)

        # 2. Alice creates a list (private by default) and shares it with the group.
        self.browser.get(self.live_server_url)
        titlebox = self.get_title_input_box()
        titlebox.send_keys("Alice Gaming List")
        titlebox.send_keys(Keys.ENTER)
        inputbox = self.get_item_input_box()
        inputbox.send_keys("Catan")
        inputbox.send_keys(Keys.ENTER)
        self.wait_for_row_in_list_table("Catan")

        wishlist = Wishlist.objects.get(title="Alice Gaming List", owner=self.alice)
        self.assertTrue(wishlist.is_private)
        self.browser.get(self.live_server_url + f"/wishlists/{wishlist.uuid}/privacy/")
        self.wait_for(
            lambda: self.browser.find_element(By.XPATH, "//label[normalize-space()='Board Game Guild']")
        ).click()
        self.browser.find_element(By.XPATH, "//button[contains(text(), 'Save Privacy Settings')]").click()
        self.wait_for(lambda: self.assertTrue(wishlist.groups.filter(name="Board Game Guild").exists()))

        # 3. Bob can't find the group on his own: the Groups page only lists his groups.
        self.browser.quit()
        self.browser = self.create_browser()
        self.create_pre_authenticated_session(username="bob@example.com", password="bobpassword123!")
        self.browser.get(self.live_server_url + "/groups/")
        self.wait_for(lambda: self.assertIn("not in any groups", self.body_text()))
        self.assertNotIn("Board Game Guild", self.body_text())

        # 4. Bob opens the invite link, sees a confirmation page, and joins.
        self.browser.get(invite_url)
        self.wait_for(lambda: self.assertIn("Join Board Game Guild?", self.body_text()))
        self.browser.find_element(By.XPATH, "//button[contains(text(), 'Join group')]").click()
        self.wait_for(lambda: self.assertIn("Leave Group", self.body_text()))
        group = _get_group_model().objects.get(name="Board Game Guild")
        self.assertTrue(group.members.filter(id=self.bob.id).exists())

        # 5. Alice's list now appears under "Shared with me" on Bob's My Lists page.
        self.browser.get(self.live_server_url + "/wishlists/lists/")
        self.wait_for(lambda: self.assertIn("Shared with me", self.body_text()))
        shared = self.browser.find_element(By.ID, "shared_lists")
        self.assertIn("Alice Gaming List", shared.text)
        self.assertIn("Board Game Guild", shared.text)

    def test_invite_link_survives_login(self):
        """An anonymous visitor following an invite link logs in and lands on the join page."""
        Group = _get_group_model()
        group = Group.objects.create(creator=self.alice, name="Board Game Guild")
        group.members.add(self.alice)
        invite_url = self.live_server_url + f"/groups/join/{group.make_invite_token()}/"

        self.browser.get(invite_url)
        self.wait_for(lambda: self.assertIn("/accounts/login/", self.browser.current_url))
        self.browser.find_element(By.NAME, "email").send_keys("bob@example.com")
        self.browser.find_element(By.NAME, "password").send_keys("bobpassword123!")
        self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        self.wait_for(lambda: self.assertIn("Join Board Game Guild?", self.body_text()))

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
