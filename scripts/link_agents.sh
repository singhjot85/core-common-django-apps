#!/usr/bin/env bash
set -euo pipefail

# Helper to compute relative path from base directory to target path
relpath() {
    local target="$1"
    local base="$2"

    local abs_target abs_base
    abs_target=$(cd "$(dirname "$target")" 2>/dev/null && pwd)/$(basename "$target")
    abs_base=$(cd "$base" 2>/dev/null && pwd)

    if [ -z "$abs_target" ] || [ -z "$abs_base" ]; then
        echo "$target"
        return
    fi

    local common="$abs_base"
    local up=""

    while [ "${abs_target#$common}" = "$abs_target" ]; do
        common=$(dirname "$common")
        up="../$up"
    done

    local remainder="${abs_target#$common}"
    remainder="${remainder#/}"
    if [ -n "$up" ]; then
        echo "${up}${remainder}"
    else
        echo "./${remainder}"
    fi
}

# Root-relative default paths (not based on script dir)
DEFAULT_SUBMODULE_AGENTS_DIR="backend/core-common-django-apps/.agents"
DEFAULT_PARENT_AGENTS_DIR=".agents"

SUBMODULE_AGENTS_DIR="${1:-${SUBMODULE_AGENTS_DIR:-$DEFAULT_SUBMODULE_AGENTS_DIR}}"
PARENT_AGENTS_DIR="${2:-${PARENT_AGENTS_DIR:-$DEFAULT_PARENT_AGENTS_DIR}}"
CATEGORY_FILTER="${3:-${CATEGORY:-}}"
ITEM_FILTER="${4:-${ITEM:-${SKILL:-}}}"
FORCE="${5:-${FORCE:-0}}"

if [ ! -d "$SUBMODULE_AGENTS_DIR" ]; then
    if [ -d "$PARENT_AGENTS_DIR" ] && [ "$SUBMODULE_AGENTS_DIR" = "$PARENT_AGENTS_DIR" ]; then
        echo "ℹ️  Already inside the submodule root ('$PARENT_AGENTS_DIR' exists locally)."
        echo "   This script is intended to be run from the parent repository to symlink submodule agent assets."
        exit 0
    fi
    echo "❌ Submodule agents directory '$SUBMODULE_AGENTS_DIR' does not exist."
    echo "💡 If running from the parent repo, ensure submodules are initialized:"
    echo "   git submodule update --init --recursive"
    echo "💡 Or override the path: make symlink-agents SUBMODULE_AGENTS_DIR=<path>"
    exit 1
fi

mkdir -p "$PARENT_AGENTS_DIR"

echo "🔗 Symlinking agents assets from '$SUBMODULE_AGENTS_DIR' to '$PARENT_AGENTS_DIR'..."
echo ""

linked_count=0

# Iterate through categories and items in SUBMODULE_AGENTS_DIR
for cat_path in "$SUBMODULE_AGENTS_DIR"/*; do
    [ -e "$cat_path" ] || continue
    category="$(basename "$cat_path")"
    [ "${category#.}" != "$category" ] && continue

    if [ -d "$cat_path" ]; then
        if [ -n "$CATEGORY_FILTER" ] && [ "$category" != "$CATEGORY_FILTER" ]; then
            continue
        fi

        dest_cat_dir="$PARENT_AGENTS_DIR/$category"
        mkdir -p "$dest_cat_dir"

        for item_path in "$cat_path"/*; do
            [ -e "$item_path" ] || continue
            item="$(basename "$item_path")"
            [ "${item#.}" != "$item" ] && continue

            if [ -n "$ITEM_FILTER" ] && [ "$item" != "$ITEM_FILTER" ]; then
                continue
            fi

            dest="$dest_cat_dir/$item"
            rel_target="$(relpath "$item_path" "$dest_cat_dir")"

            if [ -L "$dest" ]; then
                curr_target="$(readlink "$dest" || true)"
                if [ "$curr_target" = "$rel_target" ]; then
                    echo "  ✓ $category/$item -> $rel_target (already linked)"
                else
                    rm -f "$dest"
                    ln -s "$rel_target" "$dest"
                    echo "  ↻ $category/$item -> $rel_target (link updated)"
                fi
                linked_count=$((linked_count + 1))
            elif [ -e "$dest" ]; then
                if [ "$FORCE" = "1" ]; then
                    rm -rf "$dest"
                    ln -s "$rel_target" "$dest"
                    echo "  ✓ $category/$item -> $rel_target (overwrote existing $([ -d "$dest" ] && echo directory || echo file))"
                    linked_count=$((linked_count + 1))
                else
                    echo "  ⚠️  $category/$item: already exists at '$dest'. Use 'FORCE=1' to overwrite with symlink."
                fi
            else
                ln -s "$rel_target" "$dest"
                echo "  + $category/$item -> $rel_target"
                linked_count=$((linked_count + 1))
            fi
        done
    else
        # Top-level file directly under .agents
        if [ -n "$CATEGORY_FILTER" ]; then
            continue
        fi
        if [ -n "$ITEM_FILTER" ] && [ "$category" != "$ITEM_FILTER" ]; then
            continue
        fi

        dest="$PARENT_AGENTS_DIR/$category"
        rel_target="$(relpath "$cat_path" "$PARENT_AGENTS_DIR")"

        if [ -L "$dest" ]; then
            curr_target="$(readlink "$dest" || true)"
            if [ "$curr_target" = "$rel_target" ]; then
                echo "  ✓ $category -> $rel_target (already linked)"
            else
                rm -f "$dest"
                ln -s "$rel_target" "$dest"
                echo "  ↻ $category -> $rel_target (link updated)"
            fi
            linked_count=$((linked_count + 1))
        elif [ -e "$dest" ]; then
            if [ "$FORCE" = "1" ]; then
                rm -rf "$dest"
                ln -s "$rel_target" "$dest"
                echo "  ✓ $category -> $rel_target (overwrote existing file)"
                linked_count=$((linked_count + 1))
            else
                echo "  ⚠️  $category: file already exists at '$dest'. Use 'FORCE=1' to overwrite with symlink."
            fi
        else
            ln -s "$rel_target" "$dest"
            echo "  + $category -> $rel_target"
            linked_count=$((linked_count + 1))
        fi
    fi
done

echo ""
echo "✨ Done symlinking agents assets ($linked_count item(s) processed)."
