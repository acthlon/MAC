#!/usr/bin/env bash

# 1. Start the Celery worker in the background (handles background tasks like emails)
celery -A mac worker --loglevel=info --pool=solo --concurrency=1 &

# 2. Start the Celery beat scheduler in the background (if you have recurring tasks)
celery -A mac beat --loglevel=info &

# 3. Start the Django web server in the foreground
gunicorn mac.wsgi:application


