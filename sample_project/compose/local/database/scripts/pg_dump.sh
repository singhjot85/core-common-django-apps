#!/bin/sh
set -e

# If injected via Docker secrets, load from /run/secrets/db_env
if [ -f "/run/secrets/db_env" ]; then
  while IFS='=' read -r key val || [ -n "$key" ]; do
    case "$key" in
      \#*|"") continue ;;
    esac
    val=$(echo "$val" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^["'"'"']//' -e 's/["'"'"']$//')
    eval "export ${key}=\"\${${key}:-$val}\""
  done < /run/secrets/db_env
fi

# Map standard POSTGRES_* credentials to Postgres client PG* variables
export PGHOST="${PGHOST:-${POSTGRES_HOST:-postgres}}"
export PGPORT="${PGPORT:-${POSTGRES_PORT:-5432}}"
export PGUSER="${PGUSER:-${POSTGRES_USER:-postgres}}"
export PGPASSWORD="${PGPASSWORD:-${POSTGRES_PASSWORD}}"

TS=$(date +%Y%m%d_%H%M%S)

mkdir -p /backups

if [ -n "$DB_NAME" ]; then
  echo "Dumping single database: $DB_NAME..."
  pg_dump -Fc -v -d "$DB_NAME" -f "/backups/${DB_NAME}_${TS}.dump"
  echo "Dump completed successfully: /backups/${DB_NAME}_${TS}.dump"
else
  echo "DB_NAME not set. Dumping ALL databases and roles..."
  pg_dumpall -v -f "/backups/all_databases_${TS}.sql"
  echo "Dump completed successfully: /backups/all_databases_${TS}.sql"
fi
