#!/usr/bin/env bash
set -e

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Running migrations ==="
python manage.py migrate --noinput

echo "=== Seeding demo data ==="
python manage.py seed_demo

echo "=== Build complete ==="
