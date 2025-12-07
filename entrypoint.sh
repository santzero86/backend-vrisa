#!/bin/sh
set -e

echo "Aplicando migraciones de base de datos..."
python manage.py migrate

echo "Poblando la base de datos con datos semilla..."
python manage.py seed_db

exec "$@"