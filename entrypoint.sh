#!/bin/sh
set -e

if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Aplicando migraciones de base de datos..."
    python manage.py migrate

    echo "Poblando la base de datos con datos semilla..."
    python manage.py seed_db
else
    echo "Saltando migraciones y seeds (Modo Worker/Simulador)..."
fi

exec "$@"