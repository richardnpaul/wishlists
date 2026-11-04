# Standard Library Imports
import re

# Django Imports
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.core import mail
from django.test import TestCase
from django.urls import resolve, reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


User = get_user_model()


class PasswordResetURLAndRoutingTest(TestCase):
    """Verify URL routing and view class resolutions for password reset endpoints."""

    def test_password_reset_url_resolves(self):
        url = reverse("password_reset")
        self.assertEqual(url, "/accounts/password_reset/")
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, PasswordResetView)

    def test_password_reset_done_url_resolves(self):
        url = reverse("password_reset_done")
        self.assertEqual(url, "/accounts/password_reset/done/")
        resolver = resolve(url)
        # Catches routing bug where PasswordResetView was bound instead of PasswordResetDoneView
        self.assertEqual(resolver.func.view_class, PasswordResetDoneView)

    def test_password_reset_confirm_url_resolves(self):
        url = reverse(
            "password_reset_confirm",
            kwargs={"uidb64": "dummy-uid", "token": "dummy-token"},
        )
        self.assertEqual(url, "/accounts/reset/dummy-uid/dummy-token/")
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, PasswordResetConfirmView)

    def test_password_reset_complete_url_resolves(self):
        url = reverse("password_reset_complete")
        self.assertEqual(url, "/accounts/reset/done/")
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, PasswordResetCompleteView)


class PasswordResetRequestViewTest(TestCase):
    """Test initial password reset request view (GET and POST)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="registered@example.com",
            email="registered@example.com",
            password="SecurePassword123!",
        )

    def test_get_password_reset_page_renders_styled_template(self):
        response = self.client.get(reverse("password_reset"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/password_reset_form.html")
        self.assertTemplateUsed(response, "lists.base.html")
        self.assertIsInstance(response.context["form"], PasswordResetForm)
        self.assertContains(response, 'type="email"')

    def test_post_valid_email_sends_email_and_redirects_to_done(self):
        response = self.client.post(
            reverse("password_reset"),
            {"email": "registered@example.com"},
        )
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)

        sent_email = mail.outbox[0]
        self.assertIn("registered@example.com", sent_email.to)
        self.assertEqual(
            sent_email.subject.strip(),
            "Your password reset request from wishlists.richardnpaul.co.uk",
        )
        self.assertIn("/accounts/reset/", sent_email.body)

    def test_post_nonexistent_email_prevents_user_enumeration(self):
        """Django security contract: non-existent emails redirect silently without sending mail."""
        response = self.client.post(
            reverse("password_reset"),
            {"email": "unknown@example.com"},
        )
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)

    def test_post_inactive_user_does_not_send_email(self):
        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            reverse("password_reset"),
            {"email": "registered@example.com"},
        )
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)

    def test_post_invalid_email_format_renders_form_error(self):
        response = self.client.post(
            reverse("password_reset"),
            {"email": "not-a-valid-email"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/password_reset_form.html")
        self.assertEqual(len(mail.outbox), 0)
        self.assertFormError(response.context["form"], "email", "Enter a valid email address.")


class PasswordResetDoneViewTest(TestCase):
    """Test password reset done confirmation page."""

    def test_get_password_reset_done_renders_styled_template(self):
        response = self.client.get(reverse("password_reset_done"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/password_reset_done.html")
        self.assertTemplateUsed(response, "lists.base.html")
        self.assertContains(
            response,
            "We've emailed you instructions for resetting your account password",
        )


class PasswordResetConfirmViewTest(TestCase):
    """Test password reset confirmation and token validation view."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="resetuser@example.com",
            email="resetuser@example.com",
            password="OriginalPassword123!",
        )
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)
        self.valid_confirm_url = reverse(
            "password_reset_confirm",
            kwargs={"uidb64": self.uid, "token": self.token},
        )
        self.set_password_url = reverse(
            "password_reset_confirm",
            kwargs={"uidb64": self.uid, "token": "set-password"},
        )

    def test_get_confirm_with_valid_token_displays_password_form(self):
        response = self.client.get(self.valid_confirm_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/password_reset_confirm.html")
        self.assertTemplateUsed(response, "lists.base.html")
        self.assertTrue(response.context.get("validlink"))
        self.assertIsInstance(response.context.get("form"), SetPasswordForm)
        self.assertContains(response, 'name="new_password1"')
        self.assertContains(response, 'name="new_password2"')

    def test_get_confirm_with_invalid_token_shows_warning(self):
        invalid_url = reverse(
            "password_reset_confirm",
            kwargs={"uidb64": self.uid, "token": "invalid-token-xyz"},
        )
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/password_reset_confirm.html")
        self.assertFalse(response.context.get("validlink"))
        self.assertContains(response, "The password reset link was invalid")
        self.assertNotContains(response, 'name="new_password1"')

    def test_get_confirm_with_corrupted_uid_shows_warning(self):
        invalid_url = reverse(
            "password_reset_confirm",
            kwargs={"uidb64": "invalid-uid-base64", "token": self.token},
        )
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/password_reset_confirm.html")
        self.assertFalse(response.context.get("validlink"))
        self.assertContains(response, "The password reset link was invalid")

    def test_post_valid_passwords_updates_password_and_redirects(self):
        self.client.get(self.valid_confirm_url)
        new_password = "BrandNewSecurePassword123!"
        response = self.client.post(
            self.set_password_url,
            {
                "new_password1": new_password,
                "new_password2": new_password,
            },
        )
        self.assertRedirects(response, reverse("password_reset_complete"))

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))
        self.assertFalse(self.user.check_password("OriginalPassword123!"))

    def test_post_mismatched_passwords_fails_validation(self):
        self.client.get(self.valid_confirm_url)
        response = self.client.post(
            self.set_password_url,
            {
                "new_password1": "NewPassword123!",
                "new_password2": "MismatchedPassword123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/password_reset_confirm.html")

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OriginalPassword123!"))

    def test_reset_token_cannot_be_reused_after_password_change(self):
        self.client.get(self.valid_confirm_url)
        new_password = "BrandNewSecurePassword123!"
        self.client.post(
            self.set_password_url,
            {
                "new_password1": new_password,
                "new_password2": new_password,
            },
        )

        # Attempt to use the same reset link again
        second_response = self.client.get(self.valid_confirm_url)
        self.assertEqual(second_response.status_code, 200)
        self.assertFalse(second_response.context.get("validlink"))
        self.assertContains(second_response, "The password reset link was invalid")


class PasswordResetCompleteViewTest(TestCase):
    """Test password reset completion page."""

    def test_get_password_reset_complete_renders_styled_template(self):
        response = self.client.get(reverse("password_reset_complete"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/password_reset_complete.html")
        self.assertTemplateUsed(response, "lists.base.html")
        self.assertContains(response, "Your password has been set")


class PasswordResetUIExposureTest(TestCase):
    """Verify password reset link exposure on navigation dropdown and standalone login."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="loggeduser@example.com",
            email="loggeduser@example.com",
            password="Password123!",
        )

    def test_navbar_dropdown_renders_uncommented_password_reset_link_for_anon_user(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

        reset_url = reverse("password_reset")
        expected_anchor = f'href="{reset_url}"'
        self.assertContains(response, expected_anchor)
        self.assertContains(response, "Click here to reset password")

        # Verify it is not commented out
        self.assertNotContains(
            response,
            '<!--<a class="dropdown-item" href="#">Click here to reset password</a> -->',
        )

    def test_login_page_renders_uncommented_password_reset_link(self):
        response = self.client.get(reverse("account_login"))
        self.assertEqual(response.status_code, 200)

        reset_url = reverse("password_reset")
        expected_anchor = f'href="{reset_url}"'
        self.assertContains(response, expected_anchor)
        self.assertContains(response, "Click here to reset password")

        # Verify it is not commented out
        self.assertNotContains(
            response,
            '<!--<a class="dropdown-item" href="#">Click here to reset password</a> -->',
        )

    def test_authenticated_user_does_not_see_password_reset_link(self):
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Click here to reset password")


class PasswordResetEndToEndIntegrationTest(TestCase):
    """Full outside-in integration scenario testing the complete cycle."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="cycleuser@example.com",
            email="cycleuser@example.com",
            password="OldPassword123!",
        )

    def test_complete_password_reset_cycle_outside_in(self):
        # 1. User arrives at login page and sees password reset link
        login_page = self.client.get(reverse("account_login"))
        self.assertContains(login_page, reverse("password_reset"))

        # 2. User navigates to password reset form
        reset_page = self.client.get(reverse("password_reset"))
        self.assertEqual(reset_page.status_code, 200)
        self.assertTemplateUsed(reset_page, "registration/password_reset_form.html")

        # 3. User submits registered email
        post_response = self.client.post(
            reverse("password_reset"),
            {"email": "cycleuser@example.com"},
        )
        self.assertRedirects(post_response, reverse("password_reset_done"))

        # 4. Email is delivered to outbox
        self.assertEqual(len(mail.outbox), 1)
        email_body = mail.outbox[0].body

        # 5. Extract reset confirmation URL from email body
        match = re.search(r"/accounts/reset/(?P<uidb64>[^/]+)/(?P<token>[^/]+)/", email_body)
        self.assertIsNotNone(match, f"Reset URL pattern not found in email body:\n{email_body}")
        confirm_url = match.group(0)

        # 6. User clicks the reset link in the email
        confirm_page = self.client.get(confirm_url, follow=True)
        self.assertEqual(confirm_page.status_code, 200)
        self.assertTrue(confirm_page.context.get("validlink"))
        self.assertTemplateUsed(confirm_page, "registration/password_reset_confirm.html")

        # 7. User submits new password
        new_password = "NewlyMintedSecret123!"
        submit_url = confirm_page.redirect_chain[0][0] if confirm_page.redirect_chain else confirm_url
        submit_pw_response = self.client.post(
            submit_url,
            {
                "new_password1": new_password,
                "new_password2": new_password,
            },
        )
        self.assertRedirects(submit_pw_response, reverse("password_reset_complete"))

        # 8. User sees the completion page
        complete_page = self.client.get(reverse("password_reset_complete"))
        self.assertEqual(complete_page.status_code, 200)
        self.assertContains(complete_page, "Your password has been set")

        # 9. User logs in with new password
        login_response = self.client.post(
            reverse("account_login"),
            {
                "email": "cycleuser@example.com",
                "password": new_password,
            },
        )
        # Login view redirects to next_url (defaults to '/')
        self.assertEqual(login_response.status_code, 302)
        self.assertEqual(login_response.url, "/")

        # 10. Verify old password no longer works
        self.client.logout()
        failed_login = self.client.post(
            reverse("account_login"),
            {
                "email": "cycleuser@example.com",
                "password": "OldPassword123!",
            },
        )
        # Failed login re-renders login page without redirecting
        self.assertEqual(failed_login.status_code, 200)
