#!/bin/sh
set -e

VOLUME_NAME="${VOLUME_NAME:-postgres_data}"
TS=$(date +%Y%m%d_%H%M%S)
FILE="/pg_backup/${VOLUME_NAME}_${TS}.tar.gz"

mkdir -p /pg_backup
echo "Archiving volume to $FILE..."
tar -czf "$FILE" -C /pg_data .
echo "Done: $FILE"
