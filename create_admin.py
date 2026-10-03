import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAC.settings.production")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

email = "admin@marvelam.com"
password = "AdminPassword123!"

if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(email=email, password=password)
    print(f"Superuser {email} created successfully!")
else:
    print(f"Superuser {email} already exists.")
