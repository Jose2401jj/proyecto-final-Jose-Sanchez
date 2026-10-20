#!/bin/sh
set -eu

echo "Applying database migrations..."
python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
