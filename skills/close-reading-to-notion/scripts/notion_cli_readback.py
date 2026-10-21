#!/usr/bin/env python3
"""Archive a bounded set of Notion pages through ntn and check export completeness.

Read-only. These transport checks do not establish analytical quality or that an
original source has been read. Keep account-specific inputs and outputs private.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import threading
import time
import uuid


def page_id(value):
    if not isinstance(value, str):
        raise ValueError("Page identity must be a UUID string")
    return str(uuid.UUID(value))


def inspect_export(payload, expected_id):
    """Fail closed on an incomplete, unknown, or incorrectly identified export."""
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object from ntn")
    page = payload.get("page")
    markdown = payload.get("markdown")
    if not isinstance(page, dict) or not isinstance(markdown, dict):
        raise ValueError("Expected ntn JSON containing page and markdown objects")
    if page_id(page.get("id", "")) != page_id(expected_id):
        raise ValueError("Returned page identity differs from the requested page")
    if page_id(markdown.get("id", "")) != page_id(expected_id):
        raise ValueError("Markdown identity differs from the requested page")
    if markdown.get("truncated") is not False:
        raise ValueError("Export is truncated or its completeness flag is missing")
    if markdown.get("unknown_block_ids") != []:
        raise ValueError("Export contains unknown blocks or omits its block-coverage flag")
    if not isinstance(markdown.get("markdown"), str):
        raise ValueError("Export does not contain Markdown text")
    if page.get("in_trash") or page.get("is_archived"):
        raise ValueError("Requested page is archived or in Trash")
    return {"characters": len(markdown["markdown"]),
            "words": len(markdown["markdown"].split()),
            "truncated": False, "unknown_block_count": 0}


def write_private(path, text):
    path.write_text(text, encoding="utf-8")
    path.chmod(0o600)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page-id", action="append", default=[])
    parser.add_argument("--pages-file", type=Path,
                        help="Private JSON array of explicit page UUID strings")
    parser.add_argument("--output", required=True, type=Path,
                        help="New or empty private directory for this readback run")
    parser.add_argument("--workers", type=int, choices=(1, 2, 3), default=2)
    args = parser.parse_args()
    executable = shutil.which("ntn")
    if not executable:
        parser.error("ntn is unavailable; use the connected Notion tools instead")
    supplied = list(args.page_id)
    if args.pages_file:
        values = json.loads(args.pages_file.read_text())
        if not isinstance(values, list) or not all(isinstance(x, str) for x in values):
            parser.error("--pages-file must contain a JSON array of page UUID strings")
        supplied.extend(values)
    try:
        ids = [page_id(value) for value in supplied]
    except (ValueError, AttributeError) as error:
        parser.error(str(error))
    if not ids or len(ids) != len(set(ids)):
        parser.error("Provide a nonempty set of unique page UUIDs")
    destination = args.output.expanduser().resolve()
    repository = Path(__file__).resolve().parents[3]
    if destination.is_relative_to(repository):
        parser.error("Account-specific readbacks must remain outside the public repository")
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        parser.error("Use a new or empty output directory to preserve earlier readbacks")
    destination.mkdir(mode=0o700, parents=True, exist_ok=True)
    destination.chmod(0o700)
    version = subprocess.run([executable, "--version"], capture_output=True,
                             text=True, timeout=10)
    gate = threading.Lock()
    next_request = [0.0]

    def archive(identity):
        try:
            # Pace starts below three requests/second, independently of concurrency.
            with gate:
                time.sleep(max(0.0, next_request[0] - time.monotonic()))
                next_request[0] = time.monotonic() + 0.36
            result = subprocess.run([executable, "pages", "get", identity, "--json"],
                                    capture_output=True, text=True, timeout=45)
            if result.stdout:
                write_private(destination / f"{identity}.json", result.stdout)
            if result.stderr:
                write_private(destination / f"{identity}.stderr.txt", result.stderr)
            if result.returncode:
                raise ValueError(f"ntn exited {result.returncode}; inspect the private diagnostic")
            facts = inspect_export(json.loads(result.stdout), identity)
            return {"id": identity, "status": "complete_export", **facts}
        except (ValueError, OSError, subprocess.TimeoutExpired) as error:
            return {"id": identity, "status": "needs_attention", "error": str(error)}

    rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(archive, identity) for identity in ids]
        for future in as_completed(futures):
            rows.append(future.result())
    rows.sort(key=lambda row: ids.index(row["id"]))
    failures = sum(row["status"] != "complete_export" for row in rows)
    report = {"checked_at": datetime.now(timezone.utc).isoformat(),
              "cli_version": version.stdout.strip(), "requested": len(ids),
              "complete_exports": len(rows) - failures, "needs_attention": failures,
              "scope": "Export completeness and identity only; compare content and metadata separately.",
              "pages": rows}
    write_private(destination / "report.json", json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in
                      ("cli_version", "requested", "complete_exports", "needs_attention")}))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
