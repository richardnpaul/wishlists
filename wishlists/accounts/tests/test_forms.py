# Django Imports
from django.contrib.auth.models import User
from django.test import TestCase

# Local
from ..forms import LoginForm


class LoginFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            email="user.name@example.com", password='Password123!"£', first_name="User", last_name="name"
        )

    def test_login_form_is_valid(self):
        form = LoginForm(data={"email": "user.name@example.com", "password": "password"})  # Anything not blank is valid
        self.assertTrue(form.is_valid())

    def test_login_form_renders_correct_fields(self):
        form = LoginForm()
        self.assertIn('name="email"', form.as_p())
        self.assertIn('name="password"', form.as_p())
