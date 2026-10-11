from .base import *

DEBUG = True

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())
