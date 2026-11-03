from wishlists.settings.compose import *  # noqa: F401,F403


# compose.py targets AWS SES, which isn't installed or configured in development.
# Print outbound email (e.g. account activation links) to the server console instead.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
