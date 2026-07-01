#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
#  init_databases.sh
#  Runs inside the postgres container on first boot.
#  Creates:  airflow_db  (Airflow metadata)
#            retail_dw   (Data Warehouse — bronze/silver/gold)
# ─────────────────────────────────────────────────────────────────────────────
set -e

echo ">>> Creating databases: airflow_db and retail_dw ..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
    CREATE DATABASE airflow_db;
    CREATE DATABASE retail_dw;
    GRANT ALL PRIVILEGES ON DATABASE airflow_db TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON DATABASE retail_dw  TO $POSTGRES_USER;
EOSQL

echo ">>> Databases created successfully."

echo ">>> Setting up schemas in retail_dw ..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "retail_dw" \
     -f /docker-entrypoint-initdb.d/02_setup_schemas.sql

echo ">>> retail_dw setup complete."
