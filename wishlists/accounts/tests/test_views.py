# Django Imports
from django.test import TestCase

# Local
from ..forms import LoginForm


class LoginViewTest(TestCase):
    def test_displays_login_form(self):
        response = self.client.get("/accounts/login/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")
        self.assertIsInstance(response.context["login_form"], LoginForm)
