# Standard Library Imports
import time

# Django Imports
from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

# Third-party Imports
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By


MAX_WAIT = 10


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
    def create_browser(self):
        options = webdriver.FirefoxOptions()
        options.add_argument("-headless")
        return webdriver.Firefox(options=options)

    def setUp(self):
        try:
            self.browser = self.create_browser()
        except Exception as e:
            self.skipTest(f"Browser not available: {e}")

    def tearDown(self):
        if hasattr(self, "browser"):
            self.browser.quit()

    def create_pre_authenticated_session(self, username="testuser@example.com", password="password"):
        user, _ = User.objects.get_or_create(username=username, defaults={"email": username})
        user.set_password(password)
        user.save()

        session = SessionStore()
        session[SESSION_KEY] = str(user.pk)
        session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
        session[HASH_SESSION_KEY] = user.get_session_auth_hash()
        session.save()

        # To set a cookie we need to first visit the domain
        self.browser.get(self.live_server_url + "/accounts/login/")
        self.browser.add_cookie(
            {
                "name": settings.SESSION_COOKIE_NAME,
                "value": session.session_key,
                "path": "/",
            }
        )
        self.browser.get(self.live_server_url)

        # Fall back to UI login if session cookie was not picked up
        if not self.browser.find_elements(By.LINK_TEXT, "Logout"):
            self.browser.get(self.live_server_url + "/accounts/login/")
            email_field = self.browser.find_element(By.NAME, "email")
            email_field.clear()
            email_field.send_keys(username)
            pwd_field = self.browser.find_element(By.NAME, "password")
            pwd_field.clear()
            pwd_field.send_keys(password)
            self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            self.wait_for(lambda: self.browser.find_element(By.LINK_TEXT, "Logout"))
        return user

    @wait
    def wait_for(self, fn):
        return fn()

    @wait
    def wait_for_row_in_list_table(self, row_text):
        table = self.browser.find_element(By.TAG_NAME, "table")
        rows = table.find_elements(By.TAG_NAME, "tr")
        self.assertTrue(
            any(row_text in row.text for row in rows),
            f"'{row_text}' not found in any row text: {[row.text for row in rows]}",
        )

    def get_item_input_box(self):
        return self.wait_for(lambda: self.browser.find_element(By.ID, "id_text"))

    def get_title_input_box(self):
        return self.wait_for(lambda: self.browser.find_element(By.ID, "id_title"))
