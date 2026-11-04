# Standard Library Imports

# Django Imports
from django import forms
from django.conf import settings
from django.contrib.auth import SESSION_KEY, get_user_model
from django.test import TestCase
from django.urls import reverse

# Local
from accounts.forms import LoginForm


User = get_user_model()


class LoginFormRememberMeTest(TestCase):
    """Unit tests for Remember Me field in LoginForm."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="Password123!",
            first_name="Test",
            last_name="User",
        )

    def test_login_form_has_remember_me_field(self):
        """LoginForm must contain a 'remember_me' field."""
        form = LoginForm()
        self.assertIn("remember_me", form.fields)

    def test_remember_me_field_is_boolean_field(self):
        """'remember_me' field must be an instance of forms.BooleanField."""
        form = LoginForm()
        self.assertIsInstance(form.fields["remember_me"], forms.BooleanField)

    def test_remember_me_field_initial_is_true(self):
        """'remember_me' field must default to initial=True."""
        form = LoginForm()
        self.assertTrue(form.fields["remember_me"].initial)

    def test_remember_me_field_is_not_required(self):
        """'remember_me' must not be required so unchecking the checkbox passes validation."""
        form = LoginForm()
        self.assertFalse(form.fields["remember_me"].required)

    def test_unbound_form_remember_me_value_is_true(self):
        """Unbound LoginForm bound value for remember_me must evaluate to True."""
        form = LoginForm()
        self.assertTrue(form["remember_me"].value())

    def test_bound_form_valid_when_remember_me_checked_with_string_on(self):
        """When checkbox is submitted with 'on' (browser standard for checked), cleaned_data['remember_me'] is True."""
        data = {
            "email": "testuser@example.com",
            "password": "Password123!",
            "remember_me": "on",
        }
        form = LoginForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertIs(form.cleaned_data["remember_me"], True)

    def test_bound_form_valid_when_remember_me_checked_with_boolean_true(self):
        """When form receives boolean True, cleaned_data['remember_me'] is True."""
        data = {
            "email": "testuser@example.com",
            "password": "Password123!",
            "remember_me": True,
        }
        form = LoginForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertIs(form.cleaned_data["remember_me"], True)

    def test_bound_form_valid_when_remember_me_unchecked_omitted(self):
        """When checkbox is unchecked, browser omits remember_me from POST; cleaned_data['remember_me'] is False."""
        data = {
            "email": "testuser@example.com",
            "password": "Password123!",
        }
        form = LoginForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertIs(form.cleaned_data["remember_me"], False)

    def test_bound_form_valid_when_remember_me_unchecked_empty_string(self):
        """When checkbox is submitted with empty string, cleaned_data['remember_me'] is False."""
        data = {
            "email": "testuser@example.com",
            "password": "Password123!",
            "remember_me": "",
        }
        form = LoginForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertIs(form.cleaned_data["remember_me"], False)

    def test_login_form_as_p_renders_remember_me_checkbox_with_checked(self):
        """Rendering form.as_p() must include remember_me checkbox with the checked attribute."""
        form = LoginForm()
        rendered = form.as_p()
        self.assertIn('name="remember_me"', rendered)
        self.assertIn("checked", rendered)


class RememberMeTemplateRenderingTest(TestCase):
    """View/template tests verifying Remember Me checkbox defaults to checked in rendered HTML."""

    def test_login_page_renders_remember_me_checkbox_with_name_and_checked(self):
        """GET /accounts/login/ must render a checkbox with name='remember_me' and 'checked' attribute."""
        response = self.client.get(reverse("account_login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")

        content = response.content.decode("utf-8")
        # Assert input element contains name="remember_me"
        self.assertRegex(
            content,
            r'<input[^>]+name=["\']remember_me["\'][^>]*>',
            "Login page must render an input element with name='remember_me'.",
        )
        # Assert input element with name="remember_me" also has the checked attribute
        self.assertRegex(
            content,
            r'<input[^>]+name=["\']remember_me["\'][^>]+checked[^>]*>|<input[^>]+checked[^>]+name=["\']remember_me["\'][^>]*>',
            "Login page remember_me checkbox must be checked by default.",
        )
        # Assert label for remember me is present
        self.assertIn("Remember me", content)

    def test_home_page_navbar_dropdown_renders_remember_me_checkbox_with_checked(self):
        """GET / navbar dropdown login form must render remember_me checkbox checked by default."""
        response = self.client.get(reverse("home_page"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")
        self.assertTemplateUsed(response, "lists.base.html")

        content = response.content.decode("utf-8")
        # Assert navbar login dropdown renders input with name="remember_me"
        self.assertRegex(
            content,
            r'<input[^>]+name=["\']remember_me["\'][^>]*>',
            "Home page navbar login form must render an input element with name='remember_me'.",
        )
        # Assert input element with name="remember_me" has the checked attribute
        self.assertRegex(
            content,
            r'<input[^>]+name=["\']remember_me["\'][^>]+checked[^>]*>|<input[^>]+checked[^>]+name=["\']remember_me["\'][^>]*>',
            "Navbar dropdown remember_me checkbox must be checked by default.",
        )

    def test_authenticated_user_home_page_does_not_render_remember_me_checkbox(self):
        """Authenticated users visiting / should not see the login dropdown or remember_me checkbox."""
        user = User.objects.create_user(username="authuser@example.com", password="password123")
        self.client.force_login(user)
        response = self.client.get(reverse("home_page"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertNotIn('name="remember_me"', content)


class RememberMeSessionPersistenceTest(TestCase):
    """Integration tests verifying session persistence vs browser-close expiry based on Remember Me checkbox."""

    def setUp(self):
        self.email = "persisted.user@example.com"
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(
            username=self.email,
            email=self.email,
            password=self.password,
            is_active=True,
        )

    def test_login_with_remember_me_checked_persists_session(self):
        """POST /accounts/login/ with remember_me='on' configures session to persist across browser restarts."""
        response = self.client.post(
            reverse("account_login"),
            data={"email": self.email, "password": self.password, "remember_me": "on"},
        )
        # Asserts redirect upon successful authentication
        self.assertRedirects(response, "/")
        self.assertEqual(int(self.client.session[SESSION_KEY]), self.user.pk)

        # Session must NOT expire at browser close
        self.assertFalse(
            self.client.session.get_expire_at_browser_close(),
            "Session should NOT expire at browser close when remember_me is checked.",
        )

        # Expiry age must match SESSION_COOKIE_AGE
        self.assertEqual(
            self.client.session.get_expiry_age(),
            settings.SESSION_COOKIE_AGE,
            f"Session expiry age must equal settings.SESSION_COOKIE_AGE ({settings.SESSION_COOKIE_AGE}).",
        )

        # Session cookie max-age must be set to SESSION_COOKIE_AGE
        session_cookie = response.cookies.get(settings.SESSION_COOKIE_NAME)
        self.assertIsNotNone(session_cookie, "Session cookie must be returned in response.")
        self.assertEqual(
            session_cookie["max-age"],
            settings.SESSION_COOKIE_AGE,
            "Session cookie max-age must equal SESSION_COOKIE_AGE for persistent sessions.",
        )
        self.assertTrue(
            bool(session_cookie["expires"]),
            "Session cookie must have an explicit Expires date for persistent sessions.",
        )

    def test_login_with_remember_me_boolean_true_persists_session(self):
        """POST /accounts/login/ with remember_me=True configures session to persist."""
        response = self.client.post(
            reverse("account_login"),
            data={"email": self.email, "password": self.password, "remember_me": True},
        )
        self.assertRedirects(response, "/")
        self.assertEqual(int(self.client.session[SESSION_KEY]), self.user.pk)

        self.assertFalse(self.client.session.get_expire_at_browser_close())
        self.assertEqual(self.client.session.get_expiry_age(), settings.SESSION_COOKIE_AGE)

        session_cookie = response.cookies.get(settings.SESSION_COOKIE_NAME)
        self.assertEqual(session_cookie["max-age"], settings.SESSION_COOKIE_AGE)

    def test_login_without_remember_me_expires_session_on_browser_close(self):
        """POST /accounts/login/ without remember_me (unchecked) configures session to expire on browser close."""
        response = self.client.post(
            reverse("account_login"),
            data={"email": self.email, "password": self.password},
        )
        self.assertRedirects(response, "/")
        self.assertEqual(int(self.client.session[SESSION_KEY]), self.user.pk)

        # Session MUST expire at browser close
        self.assertTrue(
            self.client.session.get_expire_at_browser_close(),
            "Session MUST expire at browser close when remember_me is unchecked.",
        )

        # Session expiry internal key must be set to 0
        self.assertEqual(
            self.client.session.get("_session_expiry"),
            0,
            "Session _session_expiry must be 0 for browser-close expiration.",
        )

        # Session cookie must be a session cookie (max-age and expires are empty strings)
        session_cookie = response.cookies.get(settings.SESSION_COOKIE_NAME)
        self.assertIsNotNone(session_cookie, "Session cookie must be present.")
        self.assertEqual(
            session_cookie["max-age"],
            "",
            "Session cookie max-age must be empty for browser-close session cookies.",
        )
        self.assertEqual(
            session_cookie["expires"],
            "",
            "Session cookie expires must be empty for browser-close session cookies.",
        )

    def test_login_with_explicit_remember_me_empty_or_false_expires_on_browser_close(self):
        """POST /accounts/login/ with remember_me='' explicitly expires on browser close."""
        response = self.client.post(
            reverse("account_login"),
            data={"email": self.email, "password": self.password, "remember_me": ""},
        )
        self.assertRedirects(response, "/")
        self.assertTrue(self.client.session.get_expire_at_browser_close())
        self.assertEqual(self.client.session.get("_session_expiry"), 0)

        session_cookie = response.cookies.get(settings.SESSION_COOKIE_NAME)
        self.assertEqual(session_cookie["max-age"], "")
        self.assertEqual(session_cookie["expires"], "")

    def test_login_preserves_next_redirect_parameter_with_remember_me(self):
        """Login view preserves ?next=/target/ URL parameter while setting persistent session."""
        next_target = "/accounts/login/"  # Valid internal route
        response = self.client.post(
            f"{reverse('account_login')}?next={next_target}",
            data={"email": self.email, "password": self.password, "remember_me": "on"},
        )
        self.assertRedirects(response, next_target)
        self.assertFalse(self.client.session.get_expire_at_browser_close())

    def test_invalid_login_credentials_does_not_alter_session_or_authenticate(self):
        """Submitting wrong password must not authenticate user or persist session."""
        response = self.client.post(
            reverse("account_login"),
            data={"email": self.email, "password": "WrongPassword!", "remember_me": "on"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_inactive_user_cannot_login_and_no_session_is_created(self):
        """Inactive user submitting valid credentials must not be logged in."""
        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            reverse("account_login"),
            data={"email": self.email, "password": self.password, "remember_me": "on"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(SESSION_KEY, self.client.session)


class RememberMeSessionLifecycleTest(TestCase):
    """Verify session behavior across multiple subsequent requests and after logout."""

    def setUp(self):
        self.email = "lifecycle.user@example.com"
        self.password = "SafePassword99!"
        self.user = User.objects.create_user(
            username=self.email,
            email=self.email,
            password=self.password,
            is_active=True,
        )

    def test_persistent_session_survives_subsequent_requests(self):
        """After persistent login, subsequent HTTP requests retain authenticated state and persistence."""
        self.client.post(
            reverse("account_login"),
            data={"email": self.email, "password": self.password, "remember_me": "on"},
        )
        self.assertFalse(self.client.session.get_expire_at_browser_close())

        # Second request: Home page
        resp = self.client.get(reverse("home_page"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(self.client.session[SESSION_KEY]), self.user.pk)
        self.assertFalse(self.client.session.get_expire_at_browser_close())

    def test_browser_close_session_survives_subsequent_requests_without_persistence(self):
        """After browser-close login, subsequent HTTP requests retain authenticated state and browser-close flag."""
        self.client.post(
            reverse("account_login"),
            data={"email": self.email, "password": self.password},
        )
        self.assertTrue(self.client.session.get_expire_at_browser_close())

        # Second request: Home page
        resp = self.client.get(reverse("home_page"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(self.client.session[SESSION_KEY]), self.user.pk)
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_logout_clears_session_and_resets_state_for_next_login(self):
        """Logging out flushes session, allowing subsequent login with different persistence choice."""
        # Step 1: Login with persistent session
        self.client.post(
            reverse("account_login"),
            data={"email": self.email, "password": self.password, "remember_me": "on"},
        )
        self.assertFalse(self.client.session.get_expire_at_browser_close())

        # Step 2: Logout
        logout_resp = self.client.get(reverse("account_logout"))
        self.assertRedirects(logout_resp, reverse("home_page"))
        self.assertNotIn(SESSION_KEY, self.client.session)

        # Step 3: Login without remember_me
        self.client.post(
            reverse("account_login"),
            data={"email": self.email, "password": self.password},
        )
        self.assertEqual(int(self.client.session[SESSION_KEY]), self.user.pk)
        self.assertTrue(self.client.session.get_expire_at_browser_close())
