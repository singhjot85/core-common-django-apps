DEV_YAML_PATH = sample_project/compose/local/compose.local.yaml
PROJECT_NAME = core_common
PATH_TO_MANAGE ?= sample_project/manage.py
TEST_DIR ?= core/tests

# Database Tools Configurations & Arguments
PG_TOOLS_GRANULAR_COMPOSE ?= sample_project/compose/local/database/pg_tools_granular.yml
PG_TOOLS_VOLUME_COMPOSE ?= sample_project/compose/local/database/pg_tools.yml
DB_HOST ?= postgres
DB_PORT ?= 5432
DB_USER ?= $(or $(POSTGRES_USER),postgres)
DB_PASSWORD ?= $(or $(POSTGRES_PASSWORD),qwerty123)
DB_NAME ?=
BACKUP_FILE ?=
VOLUME_NAME ?= $(or $(STACK_NAME),core)_local_pg_data
DOCKER_NETWORK ?= $(PROJECT_NAME)_default
POSTGRES_CONTAINER ?= $(or $(STACK_NAME),core)_postgres
PG_DUMP_DIR ?=
PG_BACKUP_DIR ?=

include scripts/common.mk
