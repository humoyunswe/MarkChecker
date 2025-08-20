#!/usr/bin/env sh
set -e

python manage.py migrate --noinput

# Optionally re-collect static at runtime if desired
# python manage.py collectstatic --noinput

exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120 --access-logfile - --error-logfile -

