#!/usr/bin/env bash
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
SUBMODULE_SKILLS_DIR="${1:-backend/core-common-django-apps/.agents/skills}"
PARENT_SKILLS_DIR="${2:-.agents/skills}"
SKILL="${3:-}"
FORCE="${4:-0}"

# Derive parent agents dir and submodule agents dir
SUBMODULE_AGENTS_DIR="$(dirname "$SUBMODULE_SKILLS_DIR")"
PARENT_AGENTS_DIR="$(dirname "$PARENT_SKILLS_DIR")"

exec bash "$SCRIPT_DIR/link_agents.sh" "$SUBMODULE_AGENTS_DIR" "$PARENT_AGENTS_DIR" "skills" "$SKILL" "$FORCE"
