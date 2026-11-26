# Standard Library Imports
import re

# Django Imports
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

# Local
from ..tokens import account_activation_token


EVIL = "https://evil.example/phish"
INVITE = "/groups/join/some-token/"


class LoginNextTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="me@example.com", email="me@example.com", password="pw")
        self.creds = {"email": "me@example.com", "password": "pw"}

    def test_login_page_keeps_next_in_form_and_register_link(self):
        response = self.client.get(reverse("account_login"), {"next": INVITE})
        self.assertContains(response, f'<input type="hidden" name="next" value="{INVITE}" />', html=True)
        self.assertContains(response, "/accounts/register/?next=/groups/join/some-token/")

    def test_login_redirects_to_relative_next_from_form(self):
        response = self.client.post(reverse("account_login"), {**self.creds, "next": INVITE})
        self.assertRedirects(response, INVITE, fetch_redirect_response=False)

    def test_login_redirects_to_relative_next_from_query(self):
        response = self.client.post(f"{reverse('account_login')}?next={INVITE}", self.creds)
        self.assertRedirects(response, INVITE, fetch_redirect_response=False)

    def test_login_ignores_offsite_next(self):
        for bad in (EVIL, "//evil.example/", "javascript:alert(1)"):
            with self.subTest(next=bad):
                response = self.client.post(reverse("account_login"), {**self.creds, "next": bad})
                self.assertRedirects(response, "/", fetch_redirect_response=False)
                self.client.logout()

    def test_login_page_drops_offsite_next(self):
        response = self.client.get(reverse("account_login"), {"next": EVIL})
        self.assertNotContains(response, "evil.example")


class RegistrationNextTest(TestCase):
    data = {
        "first_name": "New",
        "last_name": "Person",
        "username": "new@example.com",
        "email": "new@example.com",
        "password1": "a-Long-unique-pw-91",
        "password2": "a-Long-unique-pw-91",
    }

    def activation_link(self):
        self.assertEqual(len(mail.outbox), 1)
        return re.search(r"https?://\S+", mail.outbox[0].body).group(0)

    def test_register_page_keeps_next(self):
        response = self.client.get(reverse("account_registration"), {"next": INVITE})
        self.assertContains(response, f'<input type="hidden" name="next" value="{INVITE}" />', html=True)

    def test_activation_email_carries_next_and_protocol(self):
        self.client.post(reverse("account_registration"), {**self.data, "next": INVITE})
        link = self.activation_link()
        self.assertTrue(link.startswith("http://"), link)
        self.assertTrue(link.endswith("?next=/groups/join/some-token/"), link)

    def test_activation_email_drops_offsite_next(self):
        self.client.post(reverse("account_registration"), {**self.data, "next": EVIL})
        self.assertNotIn("?next=", self.activation_link())

    def test_activation_follows_next_into_invite(self):
        self.client.post(reverse("account_registration"), {**self.data, "next": INVITE})
        path = "/" + self.activation_link().split("://", 1)[1].split("/", 1)[1]
        response = self.client.get(path)
        self.assertRedirects(response, INVITE, fetch_redirect_response=False)
        self.assertTrue(User.objects.get(username="new@example.com").is_active)


class ActivationRedirectTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="new@example.com", password="pw", is_active=False)
        self.url = reverse(
            "activate",
            kwargs={
                "uidb64": urlsafe_base64_encode(force_bytes(self.user.pk)),
                "token": account_activation_token.make_token(self.user),
            },
        )

    def test_activation_without_next_goes_home(self):
        self.assertRedirects(self.client.get(self.url), reverse("home_page"))

    def test_activation_ignores_offsite_next(self):
        response = self.client.get(self.url, {"next": EVIL})
        self.assertRedirects(response, reverse("home_page"))
