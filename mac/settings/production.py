import dj_database_url
from decouple import Csv, config

from .base import *
from .base import BASE_DIR

DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", cast=Csv())

DATABASES = {
    "default": dj_database_url.config(
        default=config(
            "DATABASE_URL", default="sqlite:///" + str(BASE_DIR / "db.sqlite3")
        ),
        conn_max_age=600,
    )
}

# Production Security Settings
SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
CSRF_COOKIE_SECURE = True  # Only send CSRF tokens over HTTPS
SECURE_BROWSER_XSS_FILTER = True  # Prevent cross-site scripting


# Add WhiteNoise right after SecurityMiddleware
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

# Tell WhiteNoise to compress and cache the static files
# (Legacy setting added back just to prevent django-cloudinary-storage from crashing in Django 6.0)
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}
