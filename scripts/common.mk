# Default Values (use ?= so root Makefile overrides take effect)
PROJECT_NAME ?=
DEV_YAML_PATH ?= compose/local/compose.local.yaml
DEBUGPY_YAML_PATH ?= $(dir $(DEV_YAML_PATH))compose.debugpy.yaml

# Common Variables
COMPOSE_YAML ?= $(DEV_YAML_PATH)
DJANGO_SERVICE ?= django

COMPOSE_COMMAND := docker compose --env-file .env -p $(PROJECT_NAME) -f $(or $(COMPOSE_YAML),$(DEV_YAML_PATH))
TEMP_DJANGO_CONTAINER = docker compose --env-file .env -p $(PROJECT_NAME) -f $(COMPOSE_YAML) run --rm $(DJANGO_SERVICE)
DJANGO_CONTAINER_COMMAND ?= docker compose --env-file .env -p $(PROJECT_NAME) -f $(COMPOSE_YAML) exec $(DJANGO_SERVICE)
DEBUGPY_COMPOSE_CMD ?= docker compose --env-file .env -p $(PROJECT_NAME) -f $(DEV_YAML_PATH) -f $(DEBUGPY_YAML_PATH)


# --------------------------
# Development Targets
# --------------------------
.PHONY: start-app

docker-start-new-app:
	@echo "⌛ Creating app ${APP_LABEL}...\n"
	mkdir -p core/apps/${APP_LABEL}
	$(TEMP_DJANGO_CONTAINER) python sample_project/manage.py startapp $(APP_LABEL) core/apps/$(APP_LABEL)
start-app: docker-start-new-app


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
	make run
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
	${DJANGO_CONTAINER_COMMAND} python sample_project/manage.py makemigrations ${APP_LABEL}
mm: docker-django-makemigrations

docker-django-migrate:
	@echo "⌛ Migrating Schema's now...\n"
	${DJANGO_CONTAINER_COMMAND} python sample_project/manage.py migrate
m: docker-django-migrate

docker-django-makemigrations-empty:
	@echo "⌛ Making an empty migration in App: ➡️[${APP_LABEL}] with Name: ➡️[${EMN}]...\n"
	@echo "⚠️ If this was not intended use command with 'APP_LABEL=' or 'emn=' flags"
	${DJANGO_CONTAINER_COMMAND} python sample_project/manage.py makemigrations --empty ${APP_LABEL} --name ${EMN}
mme: docker-django-makemigrations-empty


# --------------------------
# 	Shells
# --------------------------
.PHONY: bash, s, sp, ts, tsp, tsd

docker-django-bash:
	@echo "⌛ Starting bash in Django container...\n"
	${DJANGO_CONTAINER_COMMAND} bash
bash: docker-django-bash

docker-django-shell:
	@echo "⌛ Launching Django shell...\n"
	${DJANGO_CONTAINER_COMMAND} python sample_project/manage.py shell
s: docker-django-shell

docker-django-shell-plus:
	@echo "⌛ Launching Django shell-plus...\n"
	${DJANGO_CONTAINER_COMMAND} python sample_project/manage.py shell_plus --ipython
sp: docker-django-shell-plus
