from . import *

ALLOWED_HOSTS = ["*"]

DEBUG = True
SECRET_KEY = "kb^p-0d0l6n^^mx%y&neud90kl+tom9+#97y)cg%4=+-cz(^k_"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "wishlists",
        "USER": "wishlists",
        "PASSWORD": "wishlists",
        "HOST": "db",
        "PORT": "5432",
    }
}

# Social Auth Backends.
# Add all social logins before the contrib auth default
AUTHENTICATION_BACKENDS = [
    "social_core.backends.google.GoogleOAuth2",
    "social.backends.facebook.FacebookOAuth2",
    "social_core.backends.twitter.TwitterOAuth",
    "django.contrib.auth.backends.ModelBackend",
]

# Use in production for Postgres
# SOCIAL_AUTH_POSTGRES_JSONFIELD = True


# SOCIAL_AUTH_FACEBOOK_KEY = ""
# SOCIAL_AUTH_FACEBOOK_SECRET = ""
# SOCIAL_AUTH_FACEBOOK_SCOPE = ["email"]

# SOCIAL_AUTH_GOOGLE_KEY = (
#     ".apps.googleusercontent.com"
# )
# SOCIAL_AUTH_GOOGLE_SECRET = ""
# SOCIAL_AUTH_GOOGLE_SCOPE = ["email"]

LOGIN_URL = "/accounts/login/"

STATIC_ROOT = "/static/"


# Outbound email settings

# Console email backend for dev
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_BACKEND = "django_ses.SESBackend"

# Gmail accounts require additional configuration to allow direct mail through
DEFAULT_FROM_EMAIL = "webmaster@example.com"
# AWS_SES_SOURCE_ARN = "arn:aws:ses:eu-west-1:<id>:identity/<email>"

EMAIL_USE_TLS = True
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_HOST_USER = 'wishlists.email'
# EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = 2587
AWS_SES_REGION_NAME = "eu-west-1"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "/dev/stdout",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}
