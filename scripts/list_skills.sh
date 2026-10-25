#!/usr/bin/env bash
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
SUBMODULE_SKILLS_DIR="${1:-backend/core-common-django-apps/.agents/skills}"
PARENT_SKILLS_DIR="${2:-.agents/skills}"

SUBMODULE_AGENTS_DIR="$(dirname "$SUBMODULE_SKILLS_DIR")"
PARENT_AGENTS_DIR="$(dirname "$PARENT_SKILLS_DIR")"

exec bash "$SCRIPT_DIR/list_agents.sh" "$SUBMODULE_AGENTS_DIR" "$PARENT_AGENTS_DIR" "skills"
