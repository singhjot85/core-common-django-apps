#!/bin/sh
set -e

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
