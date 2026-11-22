# PostgreSQL Backup & Restore Reference Guide

A concise, conceptual reference for backing up and restoring PostgreSQL databases—covering built-in CLI tools (`pg_dump`, `pg_restore`, `pg_dumpall`), essential flags, and Docker backup strategies.

---

## 1. Core Backup Strategies

Choosing the right backup method depends on whether you need logical portability or raw filesystem snapshots:

| Strategy | Tooling | How It Works | Best Used When... |
| :--- | :--- | :--- | :--- |
| **Logical Dump (Single DB)** | `pg_dump` / `pg_restore` | Connects over TCP to a running database and exports schema + data into an archive or SQL script. | You want portable, compressed backups, single-table restores, or safe cross-version migrations. |
| **Logical Cluster Dump** | `pg_dumpall` / `psql` | Exports all databases, global roles/users, and tablespaces in a cluster into a single plain SQL file. | You need to back up multiple databases and user permissions together. |
| **Volume / Filesystem Snapshot** | `tar` / volume mounts | Archives the raw `postgres_data` directory on disk while the Postgres server is **stopped**. | You want fast, all-or-nothing snapshots of an entire Docker volume without querying over the network. |

---

## 2. Quick-Start CLI Patterns

### Custom Archive Format (`-Fc`) — Recommended
Compresses data automatically and allows selective table restores via `pg_restore`:
```bash
# Backup
pg_dump -h localhost -U my_user -Fc my_db > backup.dump

# Restore
pg_restore -h localhost -U my_user -d target_db --clean --if-exists backup.dump
```

### Plain SQL Format (`-Fp`)
Produces human-readable SQL commands; best for small databases or manual inspection:
```bash
# Backup
pg_dump -h localhost -U my_user -d my_db -f backup.sql

# Restore
psql -h localhost -U my_user -d target_db -f backup.sql
```

### Full Cluster Backup (`pg_dumpall`)
Captures all databases plus global users/roles:
```bash
# Backup
pg_dumpall -h localhost -U postgres > cluster_backup.sql

# Restore
psql -h localhost -U postgres -f cluster_backup.sql postgres
```

---

## 3. Essential `pg_dump` & `pg_restore` Flags

### Output Formats (`-F`)
* **`-Fc` (Custom):** Compressed binary archive; pairs with `pg_restore` for selective/fast restores.
* **`-Fp` (Plain SQL):** Default text format; restores via `psql`.
* **`-Fd` (Directory):** Creates a directory with one file per table; enables parallel dumps (`-j`).
* **`-Ft` (Tar):** Uncompressed tar archive compatible with `pg_restore`.

### Connection & Auth
* **`-h <host>` / `-p <port>`:** Target server hostname and port (defaults to `5432`).
* **`-U <user>` / `-d <dbname>`:** Database username and target database name.
* **`-w` / `-W`:** `-w` never prompts for a password (relies on `PGPASSWORD` or `.pgpass`); `-W` forces a prompt.
* **Environment Variables:** `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, and `PGDATABASE` are recognized natively by `pg_dump`, `pg_restore`, and `psql`.

### Filtering & Scope
* **`-t <pattern>` / `-T <pattern>`:** Include (`-t`) or exclude (`-T`) specific tables (supports wildcards like `'logs_*'`).
* **`-n <schema>` / `-N <schema>`:** Include or exclude specific schemas.
* **`-s` (`--schema-only`):** Exports structure (tables, indexes, functions) without row data.
* **`-a` (`--data-only`):** Exports row data without DDL (`CREATE TABLE`) statements.

### Restore Behavior & Cleanliness
* **`-c` (`--clean`):** Drops existing database objects before recreating them.
* **`--if-exists`:** Prevents errors when `-c` tries to drop objects that do not yet exist in the target DB.
* **`-C` (`--create`):** Includes the `CREATE DATABASE` statement in the dump/restore.
* **`-O` (`--no-owner`):** Omits object ownership commands (essential when restoring across environments with different usernames).
* **`-x` (`--no-privileges`):** Skips `GRANT` and `REVOKE` permission statements.

### Performance & Diagnostics
* **`-Z <0-9>`:** Compression level (`0` = none, `9` = max).
* **`-j <jobs>`:** Runs dump or restore across multiple CPU cores in parallel (requires `-Fd` for `pg_dump`; works with `-Fc` or `-Fd` in `pg_restore`).
* **`-v` (`--verbose`):** Outputs detailed progress logs during execution.

---

## 4. Docker Backup Concepts

### Logical Backups via Ephemeral Containers
Instead of running a full application stack (e.g., Django/Node), spin up an ephemeral **`postgres:<version>-alpine`** container attached to the same Docker network as your database container:
* **Why `postgres:alpine`:** Lightweight (<100 MB) and ships with matching `pg_dump`, `pg_restore`, and `psql` binaries pre-installed (avoiding client/server version mismatches).
* **Network & Storage:** Attach to the database's external Docker network (`--network`) to reach the DB by container/service name, and bind-mount a host directory (`-v ./pg_dump:/backups`) to persist dump files outside the ephemeral container.
* **Clean Deletion:** Before dropping a database programmatically, terminate active client connections via `pg_terminate_backend(pid)` on `pg_stat_activity`.

### Volume / Filesystem Backups
When archiving raw Docker volumes (`postgres_data:/pg_data`) using a minimal `alpine` container (`tar -czf` / `tar -xzf`):
* **Consistency Rule:** Always stop the PostgreSQL container before reading or overwriting raw volume files to prevent data corruption or incomplete WAL state.
* **Portability Caveat:** Raw volume archives are tied to the exact PostgreSQL major version and host architecture, unlike logical `pg_dump` archives.
* **SELinux Hosts:** Append `:Z` to host bind mounts (e.g., `./pg_backup:/pg_backup:Z`) on SELinux-enforcing systems like RHEL or Fedora.
