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

if [ -n "$DB_NAME" ]; then
  echo "Terminating connections and dropping database: $DB_NAME..."
  psql -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();"
  psql -d postgres -c "DROP DATABASE IF EXISTS \"$DB_NAME\";"
  echo "Database $DB_NAME dropped successfully."
else
  echo "DB_NAME not set. Dropping ALL user databases..."
  DBS=$(psql -d postgres -Atc "SELECT datname FROM pg_database WHERE datistemplate = false AND datname <> 'postgres';")
  for db in $DBS; do
    echo "Dropping $db..."
    psql -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$db' AND pid <> pg_backend_pid();"
    psql -d postgres -c "DROP DATABASE IF EXISTS \"$db\";"
  done
  echo "All non-system user databases dropped successfully."
fi
