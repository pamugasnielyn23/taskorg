#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Running Build Script..."
pip install -r requirements.txt

echo "Collecting Static Files..."
python manage.py collectstatic --no-input

echo "Running Database Migrations..."
python manage.py migrate

echo "Build Script Complete."
