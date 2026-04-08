#!/usr/bin/env bash
set -e

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Running migrations (includes permanent admin creation) ==="
python manage.py migrate --noinput

echo "=== Build complete ==="
