# Django Imports
from django.conf import settings
from django.contrib.auth import get_user_model

# Third-party Imports
from selenium.webdriver.common.by import By

# Local
from functional_tests.base import FunctionalTest


User = get_user_model()


class RememberMeFunctionalTest(FunctionalTest):
    """End-to-end Selenium browser tests for Remember Me session persistence."""

    def setUp(self):
        super().setUp()
        self.email = "e2e_user@example.com"
        self.password = "SecretE2EPassword123!"
        self.user, _ = User.objects.get_or_create(
            username=self.email,
            defaults={"email": self.email, "is_active": True},
        )
        self.user.set_password(self.password)
        self.user.save()

    def test_remember_me_checkbox_defaults_to_checked_on_login_page(self):
        """User visits /accounts/login/ and sees 'Remember me' checkbox ticked by default."""
        self.browser.get(self.live_server_url + "/accounts/login/")

        # Find the remember_me checkbox
        checkbox = self.browser.find_element(By.NAME, "remember_me")
        self.assertTrue(
            checkbox.is_selected(),
            "The 'Remember me' checkbox on /accounts/login/ should be checked by default.",
        )

    def test_remember_me_checkbox_defaults_to_checked_in_navbar_dropdown(self):
        """User visits home page and sees 'Remember me' checkbox checked in the navbar login dropdown."""
        self.browser.get(self.live_server_url)

        # Open navbar dropdown
        login_dropdown = self.browser.find_element(By.LINK_TEXT, "Login")
        login_dropdown.click()

        # Find checkbox inside dropdown
        checkbox = self.browser.find_element(By.ID, "dropdownCheck")
        self.assertTrue(
            checkbox.is_selected(),
            "The 'Remember me' checkbox in navbar dropdown should be checked by default.",
        )

    def test_login_with_remember_me_checked_sets_persistent_browser_cookie(self):
        """Logging in with remember_me checked issues a session cookie with an explicit expiry date."""
        self.browser.get(self.live_server_url + "/accounts/login/")

        # Fill credentials
        email_input = self.browser.find_element(By.NAME, "email")
        password_input = self.browser.find_element(By.NAME, "password")
        remember_checkbox = self.browser.find_element(By.NAME, "remember_me")

        email_input.send_keys(self.email)
        password_input.send_keys(self.password)

        # Confirm checkbox is selected
        self.assertTrue(remember_checkbox.is_selected())

        # Submit login form
        submit_button = self.browser.find_element(By.XPATH, "//button[@type='submit']")
        submit_button.click()

        # Wait for redirect to home
        self.wait_for_user_to_be_logged_in()

        # Check browser session cookie
        cookie = self.browser.get_cookie(settings.SESSION_COOKIE_NAME)
        self.assertIsNotNone(cookie, "Session cookie must exist after login.")
        self.assertIsNotNone(
            cookie.get("expiry"),
            "Persistent session cookie must have an 'expiry' timestamp in the browser.",
        )

    def test_login_with_remember_me_unchecked_sets_session_only_browser_cookie(self):
        """Logging in with remember_me unchecked issues a browser session-only cookie (no expiry timestamp)."""
        self.browser.get(self.live_server_url + "/accounts/login/")

        # Fill credentials
        email_input = self.browser.find_element(By.NAME, "email")
        password_input = self.browser.find_element(By.NAME, "password")
        remember_checkbox = self.browser.find_element(By.NAME, "remember_me")

        email_input.send_keys(self.email)
        password_input.send_keys(self.password)

        # Uncheck remember_me
        remember_checkbox.click()
        self.assertFalse(remember_checkbox.is_selected())

        # Submit login form
        submit_button = self.browser.find_element(By.XPATH, "//button[@type='submit']")
        submit_button.click()

        # Wait for redirect to home
        self.wait_for_user_to_be_logged_in()

        # Check browser session cookie
        cookie = self.browser.get_cookie(settings.SESSION_COOKIE_NAME)
        self.assertIsNotNone(cookie, "Session cookie must exist after login.")
        self.assertIsNone(
            cookie.get("expiry"),
            "Browser-close session cookie must NOT have an 'expiry' timestamp (session-only cookie).",
        )

    def wait_for_user_to_be_logged_in(self):
        """Helper to wait until the logout link appears, verifying login completed."""
        from functional_tests.base import wait

        @wait
        def check():
            self.browser.find_element(By.LINK_TEXT, "Logout")

        check()
