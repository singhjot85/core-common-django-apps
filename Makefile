DEV_YAML_PATH = sample_project/compose/local/compose.local.yaml
PROJECT_NAME = core_common
PATH_TO_MANAGE ?= sample_project/manage.py
TEST_DIR ?= core/tests

# Database Tools Configurations (Overrideable at runtime)
DOCKER_NETWORK ?= $(PROJECT_NAME)_default
POSTGRES_CONTAINER ?= $(or $(STACK_NAME),core)_postgres
VOLUME_NAME ?= $(or $(STACK_NAME),core)_local_pg_data
BACKUP_FILE ?=
PG_DUMP_DIR ?=
PG_BACKUP_DIR ?=
# DB_NAME ?=  # Optional: specify single database name (e.g. make db-dump DB_NAME=core_db)

include scripts/common.mk
