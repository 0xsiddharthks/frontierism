#!/usr/bin/env bash
# Link skills into Claude Code and Codex. --check only reports.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source-path=SCRIPTDIR source=../setup/lib/install-links.sh
source "$root/setup/lib/install-links.sh"
install_agent_links "$root" skills "$@"
