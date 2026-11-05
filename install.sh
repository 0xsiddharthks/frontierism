#!/usr/bin/env bash
# Runs the directory installers. By default, only skills and mods are linked;
# --all includes the Mac setup. --check only reports.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
check=false
all=false
usage() {
    echo "usage: $0 [--all] [--check]"
    echo "  default: link skills and mods"
    echo "  --all:   also run provision, dotfiles and preferences, in order"
    echo "  --check: report differences without applying changes"
}
for arg in "$@"; do
    case "$arg" in
        --all) all=true ;;
        --check) check=true ;;
        -h | --help) usage; exit 0 ;;
        *) usage >&2; exit 2 ;;
    esac
done

components=(skills mods)
if $all; then
    components=(provision dotfiles skills mods preferences)
    # Newly installed commands must be visible to the later steps in this run,
    # before the user has opened a new terminal. Keep existing PATH choices first.
    export PATH="$PATH:$HOME/.local/bin:$HOME/.cargo/bin:/opt/homebrew/bin:/usr/local/bin"
fi
mode=""
if $check; then
    mode=--check
fi
failed=0

for component in "${components[@]}"; do
    printf '\n%s\n' "$component"
    if "$root/$component/install.sh" ${mode:+"$mode"}; then
        continue
    fi
    failed=1
    if $all && ! $check; then
        echo "stopped  $component needs attention; use its installer to resolve the reported differences" >&2
        exit "$failed"
    fi
done

exit "$failed"
