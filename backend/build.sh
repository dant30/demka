#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip
python -m pip install -r django/requirements/production.txt

cd django
python manage.py collectstatic --noinput
