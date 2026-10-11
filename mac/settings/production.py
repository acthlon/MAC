from decouple import Csv, config

from .local import *

DEBUG = config("DEBUG", default=False, cast=bool)

CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", cast=Csv())


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


# CLOUDINARY SETTINGS
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": config("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": config("CLOUDINARY_API_KEY"),
    "API_SECRET": config("CLOUDINARY_API_SECRET"),
}


# Legacy setting to prevent django-cloudinary-storage from crashing in Django 6.0
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

# Tell WhiteNoise to compress and cache the static files
# (Legacy setting added back just to prevent django-cloudinary-storage from crashing in Django 6.0)
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

STORAGES = {
    # User uploaded files (pictures/videos) -> Cloudinary
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    # CSS, JavaScript, and site icons -> WhiteNoise
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}
