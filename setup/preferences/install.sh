#!/usr/bin/env bash
# Apply selected app defaults after provision and dotfiles. --check only reports.
set -euo pipefail
umask 077
root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$root/editor.py" "$@"
