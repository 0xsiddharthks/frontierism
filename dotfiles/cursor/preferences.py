#!/usr/bin/env python3
"""Sync portable Cursor preferences without copying its private application state."""

from contextlib import closing
from datetime import datetime
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys

APPLICATION_USER = (
    "src.vs.platform.reactivestorage.browser."
    "reactiveStorageServiceImpl.persistentStorage.applicationUser"
)
MODES = (
    "cmd-k", "composer", "background-composer", "plan-execution", "spec",
    "deep-search", "quick-agent", "composer-ensemble",
)
PARAMETER = {"id": str, "value": str}
MODEL = {
    "modelName": str,
    "maxMode": bool,
    "selectedModels": [{"modelId": str, "parameters": [PARAMETER]}],
}
# Deliberately name every exported field. The surrounding objects include
# credentials, team IDs, remote environments, billing and conversation state.
SCHEMA = {
    "applicationUser": {
        **{key: bool for key in (
            "cppEnabled", "systemNotificationsEnabled", "shouldOnlyImportOnAccept",
            "cppInCmdF", "cppTriggerInComments", "cppShowWhitespaceOnlyChanges",
            "indexRepository", "shouldAutoParseCmdKLinks", "autoCreateNewChatAfterTimeout",
            "isFileSyncClientEnabled", "explicitlyEnableSemanticSearch",
            "eligibleForSnippetLearning", "noStorageMode", "privacyModeVersionToggle",
            "cppAutoImportEnabled", "useModelParameters", "systemTrayEnabled",
        )},
        "cppAutoImportDecorationStyle": str,
        "composerState": {
            **{key: bool for key in (
                "alwaysKeepComposerInBound", "autoApplyFilesOutsideContext", "useYoloMode",
                "yoloMcpToolsDisabled", "yoloDeleteFileDisabled", "yoloDotFilesDisabled",
                "yoloOutsideWorkspaceDisabled", "yoloEnableRunEverything",
                "isWebSearchToolEnabled", "isWebSearchToolEnabled2", "autoAcceptWebSearchTool",
                "areSearchToolsEnabledForAskMode", "useLegacyTerminalTool", "playwrightProtection",
                "smartAllowlistEnabled", "autoAcceptGenerateImageTool", "autoApproveModeTransitions",
                "enableSmartAuto", "mcpAuthBlocking",
            )},
            **{key: str for key in (
                "maxOpenTabsMode", "location2", "defaultMode2", "codeBlockDisplayPreference",
                "thinkingLevel", "agentBackendPreference",
            )},
            "maxOpenTabsCustomValue": int,
        },
        "aiSettings": {
            "modelConfig": {mode: MODEL for mode in MODES},
            "modelDefaultSwitchOnNewChat": bool,
            "modelSettingToMaxMode": {mode: bool for mode in MODES},
            "modelOverrideEnabled": [str],
            "modelOverrideDisabled": [str],
        },
    },
    "globalStorage": {
        **{key: int for key in (
            "workbench.sideBar.size", "workbench.auxiliaryBar.size",
            "workbench.panel.size", "workbench.unifiedSidebar.size",
        )},
        "extensionsIdentifiers/disabled": [{"id": str}],
    },
}
CREDENTIAL = re.compile(
    r"(^|[^A-Za-z0-9_-])(sk-(ant-)?[A-Za-z0-9_-]{20}|gh[pousr]_[A-Za-z0-9]{30}"
    r"|github_pat_[A-Za-z0-9_]{20}|xox[abprs]-[A-Za-z0-9-]{10}|(AKIA|ASIA)[0-9A-Z]{16}"
    r"|AIza[0-9A-Za-z_-]{35})|-----BEGIN [A-Z ]*PRIVATE KEY"
    r"|(api[_-]?key|secret|token|passw(or)?d)[a-z_]*[\"']?\s*[:=]\s*[\"']?[A-Za-z0-9+/_.-]{16}",
    re.IGNORECASE | re.MULTILINE,
)
MISSING = object()


def select(value, schema):
    """Project only known fields, including inside model and parameter lists."""
    if isinstance(schema, dict):
        if not isinstance(value, dict):
            raise ValueError("Expected a preference object")
        return {key: select(value[key], child) for key, child in schema.items() if key in value}
    if isinstance(schema, list):
        if not isinstance(value, list):
            raise ValueError("Expected a preference list")
        return [select(item, schema[0]) for item in value]
    if type(value) is not schema:
        raise ValueError("Unexpected preference value type")
    return value


def read(state):
    if not state.exists():
        return {}
    with closing(sqlite3.connect(state.as_uri() + "?mode=ro", uri=True)) as connection:
        return {key: json.loads(value) for key, value in connection.execute(
            "SELECT key, value FROM ItemTable WHERE key IN (%s)"
            % ",".join("?" for _ in range(1 + len(SCHEMA["globalStorage"]))),
            [APPLICATION_USER, *SCHEMA["globalStorage"]],
        )}


def merge(current, wanted, overwrite, path, drift):
    if isinstance(wanted, dict):
        if current is MISSING:
            current = {}
        if isinstance(current, dict):
            result = current.copy()
            for key, value in wanted.items():
                result[key] = merge(current.get(key, MISSING), value, overwrite, f"{path}.{key}", drift)
            return result
    if current is MISSING or current == wanted:
        return wanted
    if overwrite:
        return wanted
    drift.append(path)
    return current


def cursor_running():
    result = subprocess.run(["pgrep", "-x", "Cursor"], capture_output=True)
    if result.returncode not in (0, 1):
        raise RuntimeError("Couldn't check whether Cursor is running")
    return result.returncode == 0


def sync(source, state, mode):
    current = read(state)
    if mode == "--pull":
        if APPLICATION_USER not in current:
            raise RuntimeError("Cursor preferences are missing; open Cursor once before pulling")
        data = select({
            "applicationUser": current[APPLICATION_USER],
            "globalStorage": {key: current[key] for key in SCHEMA["globalStorage"] if key in current},
        }, SCHEMA)
        text = json.dumps(data, indent=2) + "\n"
        if CREDENTIAL.search(text):
            raise RuntimeError("Selected Cursor preferences look like they hold a credential")
        source.write_text(text)
        print("pulled   Cursor preferences")
        return 0

    data = json.loads(source.read_text())
    if select(data, SCHEMA) != data:
        raise ValueError("Cursor preferences contain fields outside the portable allowlist")
    wanted = {APPLICATION_USER: data.get("applicationUser", {}), **data.get("globalStorage", {})}
    drift = []
    changed = {}
    for key, value in wanted.items():
        existing = current.get(key, MISSING)
        label = "Cursor application preferences" if key == APPLICATION_USER else key
        updated = merge(existing, value, mode == "--push", label, drift)
        if updated != existing:
            changed[key] = updated
    if mode == "--check":
        for key in changed:
            drift.append("Cursor application preferences" if key == APPLICATION_USER else key)
    for key in drift:
        print(f"drift    {key}: --pull keeps the app's, --push keeps this repo's")
    if mode == "--check":
        if not drift:
            print("ok       Cursor preferences")
        return int(bool(drift))
    if not changed:
        if not drift:
            print("ok       Cursor preferences")
        return int(bool(drift))
    # A running editor caches this database and could overwrite external changes.
    # Pulling and checking remain read-only and work while Cursor is open.
    if cursor_running():
        raise RuntimeError("Quit Cursor before applying its saved preferences, then run the installer again")
    existed = state.exists()
    state.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(state)) as connection:
        if existed:
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            backup = state.with_name(f"{state.name}.bak-{stamp}")
            with closing(sqlite3.connect(backup)) as destination:
                connection.backup(destination)
            # This local backup can contain account data; never put it in the repo.
            backup.chmod(0o600)
            print(f"backup   Cursor state: {backup}")
        with connection:
            connection.execute("CREATE TABLE IF NOT EXISTS ItemTable (key TEXT UNIQUE ON CONFLICT REPLACE, value BLOB)")
            connection.executemany("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                                   [(key, json.dumps(value)) for key, value in changed.items()])
    print("updated  Cursor preferences")
    return int(bool(drift))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in ("", "--check", "--pull", "--push") or len(sys.argv) > 2:
        print(f"usage: {sys.argv[0]} [--check | --pull | --push]", file=sys.stderr)
        return 2
    source = Path(__file__).with_name("preferences.json")
    state = Path.home() / "Library/Application Support/Cursor/User/globalStorage/state.vscdb"
    try:
        return sync(source, state, mode)
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as error:
        print(f"FAILED   Cursor preferences: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
