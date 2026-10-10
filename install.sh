#!/usr/bin/env bash
# Links the skills into Claude Code and Codex, and the mods into Claude Code. Safe to re-run;
# --check only reports.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
check=false
case "${1:-}" in
    "") ;;
    --check) check=true ;;
    *) echo "usage: $0 [--check]" >&2; exit 2 ;;
esac
failed=0

link() {
    local target="$1" path="$2"
    if [[ "$(readlink "$path" || true)" == "$target" ]]; then
        echo "ok       $path"
    elif $check; then
        echo "missing  $path -> $target"
        failed=1
    elif [[ -e "$path" && ! -L "$path" ]]; then
        echo "skipped  $path is a real file; move it aside and re-run"
        failed=1
    else
        mkdir -p "$(dirname "$path")"
        ln -sfn "$target" "$path"
        echo "linked   $path -> $target"
    fi
}

# ~/.agents/skills is Codex's user skills directory.
for dir in "$root"/skills/*/; do
    [[ -d "$dir" ]] || continue
    name="$(basename "$dir")"
    link "$root/skills/$name" "$HOME/.claude/skills/$name"
    link "$root/skills/$name" "$HOME/.agents/skills/$name"
done

# Claude Code loads a plugin folder it finds in its skills directory. Codex can't run a mod.
for dir in "$root"/mods/*/; do
    [[ -d "$dir" ]] || continue
    name="$(basename "$dir")"
    link "$root/mods/$name" "$HOME/.claude/skills/$name"
done

# A skill or mod that moved or was deleted leaves its old link behind.
for path in "$HOME"/.claude/skills/* "$HOME"/.agents/skills/*; do
    [[ -L "$path" && ! -e "$path" && "$(readlink "$path")" == "$root"/* ]] || continue
    if $check; then
        echo "stale    $path -> $(readlink "$path")"
        failed=1
    else
        rm "$path"
        echo "removed  $path, whose target is gone"
    fi
done

exit "$failed"
