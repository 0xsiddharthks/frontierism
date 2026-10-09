#!/usr/bin/env bash
# Copies the dotfiles here into place on macOS. A plain run adds what is missing and reports files
# that differ, without overwriting them. --check only reports, --push overwrites home's copies from
# here (keeping a backup of each), and --pull copies home's versions back here to review and commit.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mode="${1:-}"
case "$mode" in
    "" | --check | --push | --pull) ;;
    *) echo "usage: $0 [--check | --push | --pull]" >&2; exit 2 ;;
esac
failed=0
support="$HOME/Library/Application Support"
stamp="$(date +%Y%m%d-%H%M%S)"

# The apps rewrite these files, so they are copied, not linked.
files=(
    "claude/settings.json|$HOME/.claude/settings.json"
    "claude/statusline-command.sh|$HOME/.claude/statusline-command.sh"
    "ghostty/config|$support/com.mitchellh.ghostty/config"
    "herdr/config.toml|$HOME/.config/herdr/config.toml"
    "vscode/settings.json|$support/Code/User/settings.json"
    "zed/settings.json|$HOME/.config/zed/settings.json"
)

# Replaces $2 with a copy of $1, keeping the mode of the file it replaces.
copy() {
    mkdir -p "$(dirname "$2")"
    cp "$1" "$2.tmp.$$"
    if [[ -e "$2" ]]; then
        chmod "$(stat -f %Lp "$2")" "$2.tmp.$$"
    fi
    mv "$2.tmp.$$" "$2"
}

for entry in "${files[@]}"; do
    src="$root/${entry%%|*}"
    dst="${entry#*|}"
    if [[ ! -e "$dst" ]]; then
        if [[ "$mode" == --check || "$mode" == --pull ]]; then
            echo "missing  $dst"
            failed=1
        else
            copy "$src" "$dst"
            echo "copied   $dst"
        fi
    elif cmp -s "$src" "$dst"; then
        echo "ok       $dst"
    elif [[ "$mode" == --push ]]; then
        cp -p "$dst" "$dst.bak-$stamp"
        copy "$src" "$dst"
        echo "updated  $dst (the old one is $dst.bak-$stamp)"
    elif [[ "$mode" == --pull ]]; then
        copy "$dst" "$src"
        echo "pulled   $dst"
    else
        echo "drift    $dst differs: --pull keeps home's, --push keeps this repo's"
        failed=1
    fi
done

list="$root/vscode/extensions.txt"
if ! command -v code >/dev/null; then
    echo "skipped  VS Code extensions: the code command isn't on PATH"
    failed=1
elif ! installed="$(code --list-extensions)"; then
    echo "FAILED   VS Code extensions: couldn't list the installed ones"
    failed=1
elif [[ "$mode" == --pull ]]; then
    sort -f <<<"$installed" >"$list.tmp.$$"
    mv "$list.tmp.$$" "$list"
    echo "pulled   VS Code extensions"
else
    installed="$(tr '[:upper:]' '[:lower:]' <<<"$installed")"
    missing=0
    while IFS= read -r extension; do
        [[ -n "$extension" ]] || continue
        if grep -qxF "$(tr '[:upper:]' '[:lower:]' <<<"$extension")" <<<"$installed"; then
            continue
        fi
        missing=1
        if [[ "$mode" == --check ]]; then
            echo "missing  VS Code extension $extension"
            failed=1
        elif code --install-extension "$extension" >/dev/null; then
            echo "added    VS Code extension $extension"
        else
            echo "FAILED   VS Code extension $extension"
            failed=1
        fi
    done <"$list"
    if [[ "$missing" == 0 ]]; then
        echo "ok       VS Code extensions"
    fi
fi

exit "$failed"
