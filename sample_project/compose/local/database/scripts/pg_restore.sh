#!/bin/sh
set -e

if [ -z "$BACKUP_FILE" ]; then
  echo "Error: Set BACKUP_FILE to a filename inside ./pg_dump (e.g., BACKUP_FILE=mydb_20261122_124500.dump)" >&2
  exit 1
fi

if [ ! -f "/backups/$BACKUP_FILE" ]; then
  echo "Error: Backup file /backups/$BACKUP_FILE does not exist!" >&2
  exit 1
fi

if [ -n "$DB_NAME" ]; then
  echo "Restoring single database: $DB_NAME from $BACKUP_FILE..."
  psql -d postgres -c "CREATE DATABASE \"$DB_NAME\";" 2>/dev/null || true
  pg_restore --clean --if-exists --no-owner -x -v -d "$DB_NAME" "/backups/$BACKUP_FILE"
  echo "Restore completed successfully for database: $DB_NAME"
else
  echo "DB_NAME not set. Restoring ALL databases from $BACKUP_FILE..."
  psql -v ON_ERROR_STOP=1 -d postgres -f "/backups/$BACKUP_FILE"
  echo "Cluster restore completed successfully from $BACKUP_FILE."
fi
