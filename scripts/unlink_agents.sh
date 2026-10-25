#!/usr/bin/env bash
set -euo pipefail

DEFAULT_SUBMODULE_AGENTS_DIR="backend/core-common-django-apps/.agents"
DEFAULT_PARENT_AGENTS_DIR=".agents"

SUBMODULE_AGENTS_DIR="${1:-${SUBMODULE_AGENTS_DIR:-$DEFAULT_SUBMODULE_AGENTS_DIR}}"
PARENT_AGENTS_DIR="${2:-${PARENT_AGENTS_DIR:-$DEFAULT_PARENT_AGENTS_DIR}}"
CATEGORY_FILTER="${3:-${CATEGORY:-}}"
ITEM_FILTER="${4:-${ITEM:-${SKILL:-}}}"

if [ ! -d "$PARENT_AGENTS_DIR" ]; then
    echo "Parent agents directory '$PARENT_AGENTS_DIR' does not exist."
    exit 0
fi

echo "🗑️  Unlinking agents assets from '$PARENT_AGENTS_DIR'..."
echo ""

unlinked_count=0

for cat_path in "$PARENT_AGENTS_DIR"/*; do
    [ -e "$cat_path" ] || continue
    category="$(basename "$cat_path")"
    [ "${category#.}" != "$category" ] && continue

    if [ -d "$cat_path" ] && [ ! -L "$cat_path" ]; then
        if [ -n "$CATEGORY_FILTER" ] && [ "$category" != "$CATEGORY_FILTER" ]; then
            continue
        fi

        for item_path in "$cat_path"/*; do
            [ -e "$item_path" ] || [ -L "$item_path" ] || continue
            item="$(basename "$item_path")"
            [ "${item#.}" != "$item" ] && continue

            if [ -n "$ITEM_FILTER" ] && [ "$item" != "$ITEM_FILTER" ]; then
                continue
            fi

            if [ -L "$item_path" ]; then
                target="$(readlink "$item_path" || true)"
                rm -f "$item_path"
                echo "  - Unlinked $category/$item (was -> $target)"
                unlinked_count=$((unlinked_count + 1))
            elif [ -e "$item_path" ]; then
                echo "  ⚠️  $category/$item is a real $([ -d "$item_path" ] && echo directory || echo file), skipped."
            fi
        done

        # Remove empty category directory if no items left
        rmdir "$cat_path" 2>/dev/null || true
    elif [ -L "$cat_path" ]; then
        if [ -n "$CATEGORY_FILTER" ] && [ "$category" != "$CATEGORY_FILTER" ]; then
            continue
        fi
        if [ -n "$ITEM_FILTER" ] && [ "$category" != "$ITEM_FILTER" ]; then
            continue
        fi

        target="$(readlink "$cat_path" || true)"
        rm -f "$cat_path"
        echo "  - Unlinked $category (was -> $target)"
        unlinked_count=$((unlinked_count + 1))
    fi
done

echo ""
echo "✨ Unlinked $unlinked_count item(s)."
