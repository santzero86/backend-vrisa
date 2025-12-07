#!/bin/sh
set -e

echo "Aplicando migraciones de base de datos..."
python manage.py migrate

exec "$@"