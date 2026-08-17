"""
Settings used by the test suite.

    python manage.py test --settings=config.settings_test

Runs against an in-memory SQLite database so the suite needs no PostgreSQL
server, and switches off the production hardening that would otherwise turn
every test request into a 301 redirect to HTTPS.
"""

import os

# config.settings reads these through python-decouple and would raise on a
# machine without a .env; the values are irrelevant to the tests themselves.
# At least 32 bytes, or PyJWT warns on every token signed during the suite.
os.environ.setdefault(
    "SECRET_KEY", "test-only-not-a-real-secret-padded-to-32-bytes-minimum"
)
os.environ.setdefault("DB_NAME", "test")

from .settings import *  # noqa: F403,E402

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# The `if not DEBUG` block in settings.py turns these on. Under the test client
# every request would then answer 301 instead of reaching the view.
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Hashing is the single slowest thing in an auth-heavy suite.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Throttling would start rejecting requests part-way through the suite. The
# rates are raised rather than removed: views that name a scope explicitly keep
# their throttle class, and an unknown scope raises ImproperlyConfigured.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_CLASSES": (),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "10000/min",
        "user": "10000/min",
        "auth": "10000/min",
    },
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
