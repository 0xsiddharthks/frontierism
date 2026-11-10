#!/usr/bin/env bash
# Configure the manually installed Mac app. No downloads, sudo or server restarts.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mode="${1:-}"
case "$mode" in
    "" | --check | --push | --pull) ;;
    *) echo "usage: $0 [--check | --push | --pull]" >&2; exit 2 ;;
esac

# Always configure this Mac, even if the installer was run inside another Rex
# session. The launcher normally prefers the CLI of its inherited Rex server.
rex_local() {
    env -u REX_BIN_DIR -u REX_SERVER -u REX_SESSION -u REX_BLOCK -u REX_CLIENT -u REX_CONFIG \
        "$root/rex" "$@"
}

if [[ "$mode" == --pull ]]; then
    exec python3 "$root/preferences.py" --pull
fi
rex_local version >/dev/null
echo "ok       Rex app and bundled CLI"
failed=0
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

completion="${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_rex"
rex_local completion zsh >"$tmp/_rex"
if cmp -s "$tmp/_rex" "$completion"; then
    echo "ok       Rex Zsh completion"
elif [[ "$mode" == --check ]]; then
    echo "missing  Rex Zsh completion; run the dotfile installer"
    failed=1
else
    mkdir -p "$(dirname "$completion")"
    cp "$tmp/_rex" "$completion"
    echo "updated  Rex Zsh completion"
fi

if [[ "$mode" == --check ]]; then
    rex_local skill status --json >"$tmp/skills.json"
    python3 - "$tmp/skills.json" <<'PY' || failed=1
import json, sys
data = json.load(open(sys.argv[1]))
failed = False
for name in ("claude", "codex"):
    harness = next((h for h in data["harnesses"] if h["id"] == name), None)
    items = harness["items"] if harness else []
    for kind in ("skill", "hook"):
        item = next((i for i in items if i["kind"] == kind), {})
        state = item.get("state", "missing")
        print(f'{"ok" if state == "current" else state:8} Rex {name} {kind}')
        failed |= state != "current"
sys.exit(int(failed))
PY
    rex_local terminfo status --json >"$tmp/terminfo.json"
    python3 - "$tmp/terminfo.json" <<'PY' || failed=1
import json, sys
status = json.load(open(sys.argv[1]))
ready = status.get("auto_term") == "xterm-rex"
print(f'{"ok" if ready else "missing":8} Rex terminfo and SSH fallback')
if not ready:
    print("note     " + status.get("fix", "run rex terminfo setup"))
sys.exit(int(not ready))
PY
else
    # Rex merges its own hooks and leaves unrelated settings and skills intact.
    rex_local skill setup --agent claude --agent codex
    # Installs the terminal description and an SSH Include guard. Unknown
    # remote hosts receive xterm-256color instead of an unknown terminal type.
    rex_local terminfo setup
fi

python3 "$root/preferences.py" "$mode" || failed=1
config="${XDG_CONFIG_HOME:-$HOME/.config}/rex/init.lua"
rex_local config check "$config" || failed=1
if [[ "$mode" != --check && "$failed" == 0 ]]; then
    if rex_local --autostart=false server status >/dev/null 2>&1; then
        rex_local --autostart=false config reload || failed=1
    else
        echo "note     open Rex to load its configuration"
    fi
fi
exit "$failed"
