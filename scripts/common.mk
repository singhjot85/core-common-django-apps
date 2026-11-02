# Default Values (use ?= so root Makefile overrides take effect)
PROJECT_NAME ?=
DEV_YAML_PATH ?=
DEBUGPY_YAML_PATH ?= $(dir $(DEV_YAML_PATH))compose.debugpy.yaml
PATH_TO_MANAGE ?=

# Common Variables
COMPOSE_YAML ?= $(DEV_YAML_PATH)
DJANGO_SERVICE ?= django
CACHE_SERVICE ?= cache
BROKER_SERVICE ?= broker
TEST_DIR ?=
TEST_FILTER ?=
CMD ?= 		# Generic Variable to be used as override for commands
POETRY_COMMAND ?= install --no-root
DEFAULT_TENANT_SCHEMA ?=
# Agents Symlink Variables (paths relative to root)
CURRENT_COMMON_MK_DIR := $(patsubst %/,%,$(dir $(lastword $(MAKEFILE_LIST))))
SCRIPTS_DIR ?= $(CURRENT_COMMON_MK_DIR)
SUBMODULE_DIR ?= $(or $(patsubst %/scripts,%,$(SCRIPTS_DIR)),backend/core-common-django-apps)
SUBMODULE_AGENTS_DIR ?= $(or $(SUBMODULE_SKILLS_DIR),$(if $(filter-out scripts,$(SCRIPTS_DIR)),$(SUBMODULE_DIR)/.agents,.agents))
PARENT_AGENTS_DIR ?= $(or $(PARENT_SKILLS_DIR),.agents)
CATEGORY ?=
ITEM ?=
SKILL ?=
FORCE ?= 0

COMPOSE_COMMAND = docker compose --env-file ./.env -p $(PROJECT_NAME) -f $(or $(COMPOSE_YAML),$(DEV_YAML_PATH))
DJANGO_CONTAINER_COMMAND = docker compose --env-file ./.env -p $(PROJECT_NAME) -f $(COMPOSE_YAML) exec $(DJANGO_SERVICE)
TEMP_DJANGO_CONTAINER = docker compose --env-file ./.env -p $(PROJECT_NAME) -f $(COMPOSE_YAML) run --rm $(DJANGO_SERVICE)
# DEBUGPY_COMPOSE_CMD = export ENABLE_DEBUGPY=1 && $(COMPOSE_COMMAND)
DEBUGPY_COMPOSE_CMD ?= docker compose --env-file ./.env -p $(PROJECT_NAME) -f $(DEV_YAML_PATH) -f $(DEBUGPY_YAML_PATH) run -p ${DEBUGPY_DJANGO_PORT}:5678 --rm ${DJANGO_SERVICE} python -m debugpy --listen 0.0.0.0:5678
DEBUGPY_TEMP_DJANGO_CONTAINER ?= docker compose --env-file ./.env -p $(PROJECT_NAME) -f $(DEV_YAML_PATH) -f $(DEBUGPY_YAML_PATH) run -p ${DEBUGPY_DJANGO_PORT}:5678 --rm ${DJANGO_SERVICE} python -m debugpy --listen 0.0.0.0:5678

CACHE_CONTAINER_COMMAND ?= docker compose --env-file .env -p $(PROJECT_NAME) -f $(COMPOSE_YAML) exec $(CACHE_SERVICE)
BROKER_CONTAINER_COMMAND ?= docker compose --env-file .env -p $(PROJECT_NAME) -f $(COMPOSE_YAML) exec $(BROKER_SERVICE)

# Import the envoiurnment variables
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# --------------------------
# Development Targets
# --------------------------
.PHONY: start-app, seed-tenants, seed-models, setup, clean-setup

docker-start-new-app:
	@echo "⌛ Creating app ${APP_LABEL}...\n"
	mkdir -p core/apps/${APP_LABEL}
	$(TEMP_DJANGO_CONTAINER) python ${PATH_TO_MANAGE} startapp $(APP_LABEL) core/apps/$(APP_LABEL)
start-app: docker-start-new-app

docker-seed-tenants:
	@echo "⌛ Seeding development tenants in current env...\n"
	$(TEMP_DJANGO_CONTAINER) python ${PATH_TO_MANAGE} add_dev_tenants
seed-tenants: docker-seed-tenants

docker-seed-models:
	@echo "⌛ Running development setup and seeders...\n"
	$(TEMP_DJANGO_CONTAINER) python ${PATH_TO_MANAGE} run_dev_seeders
seed-models: docker-seed-models

docker-dev-setup:
	@echo "⌛ Running complete development setup...\n"
	make rund
	make m
	make seed-tenants
	make seed-models
setup: docker-dev-setup

docker-dev-clean-setup:
	@echo "⚠️ Cleaning exisiting database...\n"
	make db-destroy
	make setup
clean-setup: docker-dev-clean-setup


# --------------------------
# 		Builds
# --------------------------
.PHONY: build, rebuild, clean, cbr, run, run-d, vscode-debug, db-destroy

docker-build:
	@echo "⌛ Starting build process...\n"
	@echo "⚠️ This stage might pull images make sure you are connected"
	${COMPOSE_COMMAND} build
build: docker-build

docker-rebuild:
	@echo "⌛ Putting down containers build process...\n"
	${COMPOSE_COMMAND} down
	make build
	make rund
rebuild: docker-rebuild

docker-clean-project:
	@echo "☣️ Cleaning entire project: Containers, Volumes, Compose Images, Orphan containers"
	${COMPOSE_COMMAND} down --volumes --rmi all --remove-orphans
clean: docker-clean-project

docker-clean-build-run:
	make clean
	make build
	make m
	make run
cbr: docker-clean-build-run

docker-run:
	@echo "⌛ Starting containers...\n"
	${COMPOSE_COMMAND} up
run: docker-run

docker-detached-run:
	@echo "⌛ Starting containers...\n"
	${COMPOSE_COMMAND} up -d
rund: docker-detached-run

docker-debugpy-vscode-debug:
	@echo "⌛ Running containers and attaching debugpy...\n"
	${DEBUGPY_COMPOSE_CMD} up --remove-orphans
vscode-debug: docker-debugpy-vscode-debug

docker-destroy-database:
	${COMPOSE_COMMAND} down --volumes
db-destroy: docker-destroy-database


# --------------------------
# 	Migrations
# --------------------------
.PHONY: mm, m, mme

docker-django-makemigrations:
	@echo "⌛ Making migrations in App: ➡️[${APP_LABEL}]...\n"
	@echo "⚠️ If this was not intended use command with APP_LABEL= flag"
	${TEMP_DJANGO_CONTAINER} python ${PATH_TO_MANAGE} makemigrations ${APP_LABEL}
mm: docker-django-makemigrations

docker-django-migrate:
	@echo "⌛ Migrating Schema's now...\n"
	${TEMP_DJANGO_CONTAINER} python ${PATH_TO_MANAGE} migrate
m: docker-django-migrate

docker-django-makemigrations-empty:
	@echo "⌛ Making an empty migration in App: ➡️[${APP_LABEL}] with Name: ➡️[${EMN}]...\n"
	@echo "⚠️ If this was not intended use command with 'APP_LABEL=' or 'emn=' flags"
	${TEMP_DJANGO_CONTAINER} python ${PATH_TO_MANAGE} makemigrations --empty ${APP_LABEL} --name ${EMN}
mme: docker-django-makemigrations-empty


# --------------------------
# 	Pytest Targets
# # --------------------------
.PHONY: t, td, tf, test

docker-django-pytest:
	@echo "⌛ Running tests...\n"
	${TEMP_DJANGO_CONTAINER} pytest ${TEST_DIR}
t: docker-django-pytest
test: docker-django-pytest

docker-django-pytest-filter:
	@echo "⌛ Running tests...\n"
	${TEMP_DJANGO_CONTAINER} pytest -k ${TEST_FILTER}
tf: docker-django-pytest

docker-django-pytest-debug:
	@echo "⌛ Running tests with debugger...\n"
	${DEBUGPY_TEMP_DJANGO_CONTAINER} pytest ${TEST_DIR}
td: docker-django-pytest-debug

# --------------------------
# 	Shells
# --------------------------
.PHONY: bash, s, sp, ts, tsp, tsd, broker-cli, cache-cli

docker-django-bash:
	@echo "⌛ Starting bash in Django container...\n"
	${TEMP_DJANGO_CONTAINER} bash
bash: docker-django-bash

docker-django-shell:
	@echo "⌛ Launching Django shell...\n"
	${TEMP_DJANGO_CONTAINER} python ${PATH_TO_MANAGE} shell
s: docker-django-shell

docker-django-shell-plus:
	@echo "⌛ Launching Django shell-plus...\n"
	${TEMP_DJANGO_CONTAINER} python ${PATH_TO_MANAGE} shell_plus --ipython
sp: docker-django-shell-plus

docker-django-tenant-shell:
	@echo "⌛ Launching Django Tenant shell...\n"
	${TEMP_DJANGO_CONTAINER} python ${PATH_TO_MANAGE} tenant_command shell --schema=${DEFAULT_TENANT_SCHEMA}
ts: docker-django-tenant-shell

docker-django-tenant-shell-debug:
	@echo "⌛ Launching Django Tenant shell with debugpy...\n"
	${DEBUGPY_TEMP_DJANGO_CONTAINER} ${PATH_TO_MANAGE} tenant_command shell --schema=${DEFAULT_TENANT_SCHEMA}
tsd: docker-django-tenant-shell-debug

docker-django-tenant-shell-plus:
	@echo "⌛ Launching Django Tenant shell plus...\n"
	${TEMP_DJANGO_CONTAINER} python ${PATH_TO_MANAGE} tenant_command shell_plus --schema=${DEFAULT_TENANT_SCHEMA}
tsp: docker-django-tenant-shell-plus

docker-django-tenant-shell-plus-debug:
	@echo "⌛ Launching Django Tenant shell plus...\n"
	${DEBUGPY_TEMP_DJANGO_CONTAINER} ${PATH_TO_MANAGE} tenant_command shell_plus --schema=${DEFAULT_TENANT_SCHEMA}
tspd: docker-django-tenant-shell-plus-debug

docker-cache-cli:
	@echo "⌛ Launching redis-cli for cache service ${CACHE_SERVICE}...\n"
	${CACHE_CONTAINER_COMMAND} redis-cli -p ${CACHE_PORT}
cache-cli: docker-cache-cli

docker-broker-cli:
	@echo "⌛ Launching redis-cli for cache service ${CACHE_SERVICE}...\n"
	${BROKER_CONTAINER_COMMAND} redis-cli -p ${BROKER_PORT}
broker-cli: docker-broker-cli


# --------------------------
# 	Common Dev targets
# --------------------------
.PHONY: poetry

docker-poetry:
	@echo "⌛ Executing poetry command $(if $(CMD),$(CMD),$(POETRY_COMMAND))..."
	${TEMP_DJANGO_CONTAINER} poetry $(if $(CMD),$(CMD),$(POETRY_COMMAND))
poetry: docker-poetry

# --------------------------
# 	Agents Management
# --------------------------
.PHONY: symlink-agents, link-agents, unlink-agents, remove-agents-links, list-agents, status-agents
.PHONY: symlink-skills, link-skills, unlink-skills, remove-skills-links, list-skills, status-skills

symlink-agents:
	@bash $(SCRIPTS_DIR)/link_agents.sh "$(SUBMODULE_AGENTS_DIR)" "$(PARENT_AGENTS_DIR)" "$(CATEGORY)" "$(if $(ITEM),$(ITEM),$(SKILL))" "$(FORCE)"
link-agents: symlink-agents
symlink-skills: symlink-agents
link-skills: symlink-agents

unlink-agents:
	@bash $(SCRIPTS_DIR)/unlink_agents.sh "$(SUBMODULE_AGENTS_DIR)" "$(PARENT_AGENTS_DIR)" "$(CATEGORY)" "$(if $(ITEM),$(ITEM),$(SKILL))"
remove-agents-links: unlink-agents
unlink-skills: unlink-agents
remove-skills-links: unlink-agents

list-agents:
	@bash $(SCRIPTS_DIR)/list_agents.sh "$(SUBMODULE_AGENTS_DIR)" "$(PARENT_AGENTS_DIR)" "$(CATEGORY)"
status-agents: list-agents
list-skills: list-agents
status-skills: list-agents
