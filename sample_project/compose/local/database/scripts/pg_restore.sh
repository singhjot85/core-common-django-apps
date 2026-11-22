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

if [ -z "$BACKUP_FILE" ]; then
  echo "Error: Set BACKUP_FILE to a filename inside ./pg_dump (e.g., BACKUP_FILE=mydb_20261122_124500.dump)" >&2
  exit 1
fi

if [ ! -f "/backups/$BACKUP_FILE" ]; then
  if [ -f "/backups/${BACKUP_FILE}.sql" ]; then
    BACKUP_FILE="${BACKUP_FILE}.sql"
  elif [ -f "/backups/${BACKUP_FILE}.dump" ]; then
    BACKUP_FILE="${BACKUP_FILE}.dump"
  else
    echo "Error: Backup file /backups/$BACKUP_FILE does not exist!" >&2
    exit 1
  fi
fi

if [ -n "$DB_NAME" ]; then
  echo "Restoring single database: $DB_NAME from $BACKUP_FILE..."
  psql -d postgres -c "CREATE DATABASE \"$DB_NAME\";" 2>/dev/null || true
  pg_restore --clean --if-exists --no-owner -x -v -d "$DB_NAME" "/backups/$BACKUP_FILE"
  echo "Restore completed successfully for database: $DB_NAME"
else
  echo "DB_NAME not set. Restoring ALL databases from $BACKUP_FILE..."
  # Strip LOCALE_PROVIDER if present (incompatible with PostgreSQL 14) and allow benign role creation notices
  sed 's/LOCALE_PROVIDER = [^ ]* //g' "/backups/$BACKUP_FILE" | psql -d postgres
  echo "Cluster restore completed successfully from $BACKUP_FILE."
fi
