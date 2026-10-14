import dj_database_url

from .base import *

DEBUG = True

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())

DATABASE_URL = config("DATABASE_URL", default="")


DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
    )
}
DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True  # ceeck yhis out
