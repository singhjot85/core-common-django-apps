#!/bin/sh
set -e

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
