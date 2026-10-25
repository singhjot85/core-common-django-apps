#!/usr/bin/env bash
set -euo pipefail

DEFAULT_SUBMODULE_AGENTS_DIR="backend/core-common-django-apps/.agents"
DEFAULT_PARENT_AGENTS_DIR=".agents"

SUBMODULE_AGENTS_DIR="${1:-${SUBMODULE_AGENTS_DIR:-$DEFAULT_SUBMODULE_AGENTS_DIR}}"
PARENT_AGENTS_DIR="${2:-${PARENT_AGENTS_DIR:-$DEFAULT_PARENT_AGENTS_DIR}}"
CATEGORY_FILTER="${3:-${CATEGORY:-}}"

if [ ! -d "$SUBMODULE_AGENTS_DIR" ]; then
    echo "❌ Submodule agents directory '$SUBMODULE_AGENTS_DIR' does not exist."
    exit 1
fi

echo "📋 Agents Directory Status ('$SUBMODULE_AGENTS_DIR' -> '$PARENT_AGENTS_DIR'):"
echo ""

found_any=0

for cat_path in "$SUBMODULE_AGENTS_DIR"/*; do
    [ -e "$cat_path" ] || continue
    category="$(basename "$cat_path")"
    [ "${category#.}" != "$category" ] && continue

    if [ -d "$cat_path" ]; then
        if [ -n "$CATEGORY_FILTER" ] && [ "$category" != "$CATEGORY_FILTER" ]; then
            continue
        fi

        found_any=1
        echo "[$category]"
        for item_path in "$cat_path"/*; do
            [ -e "$item_path" ] || continue
            item="$(basename "$item_path")"
            [ "${item#.}" != "$item" ] && continue

            dest="$PARENT_AGENTS_DIR/$category/$item"
            if [ -L "$dest" ]; then
                target="$(readlink "$dest" || true)"
                status="🔗 LINKED -> $target"
            elif [ -d "$dest" ]; then
                status="📁 DIRECTORY (not symlinked)"
            elif [ -e "$dest" ]; then
                status="📄 FILE (not symlinked)"
            else
                status="❌ NOT LINKED"
            fi
            printf "  %-25s %s\n" "$item" "$status"
        done
        echo ""
    else
        # Top-level file
        if [ -n "$CATEGORY_FILTER" ]; then
            continue
        fi
        found_any=1
        dest="$PARENT_AGENTS_DIR/$category"
        if [ -L "$dest" ]; then
            target="$(readlink "$dest" || true)"
            status="🔗 LINKED -> $target"
        elif [ -e "$dest" ]; then
            status="📄 FILE (not symlinked)"
        else
            status="❌ NOT LINKED"
        fi
        printf "  %-25s %s\n" "$category" "$status"
    fi
done

if [ "$found_any" -eq 0 ]; then
    echo "⚠️  No agent items found in '$SUBMODULE_AGENTS_DIR'."
fi
