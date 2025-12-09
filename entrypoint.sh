#!/bin/sh
set -e

if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Aplicando migraciones de base de datos..."
    python manage.py migrate

    echo "Poblando la base de datos con datos semilla..."
    python manage.py seed_db

    echo "[3/3] Verificando y generando histórico de datos (Últimos 30 días)..."
    python manage.py seed_history
else
    echo "Saltando migraciones y seeds (Modo Worker/Simulador)..."
fi

exec "$@"