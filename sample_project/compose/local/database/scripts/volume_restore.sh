#!/bin/sh
set -e

if [ -z "$BACKUP_FILE" ]; then
  echo "Error: Set BACKUP_FILE to a .tar.gz filename inside ./pg_backup" >&2
  exit 1
fi

if [ ! -f "/pg_backup/$BACKUP_FILE" ]; then
  echo "Error: /pg_backup/$BACKUP_FILE not found!" >&2
  exit 1
fi

echo "Wiping existing volume contents in /pg_data..."
rm -rf /pg_data/* /pg_data/.[!.]* /pg_data/..?* 2>/dev/null || true
echo "Restoring $BACKUP_FILE into volume..."
tar -xzf "/pg_backup/$BACKUP_FILE" -C /pg_data
echo "Restore complete. You can now start your Postgres container."
