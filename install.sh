#!/usr/bin/env bash
# Links the skills into Claude Code and Codex. Safe to re-run; --check only reports.
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

exit "$failed"
