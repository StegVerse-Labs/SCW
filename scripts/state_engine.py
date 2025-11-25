#!/usr/bin/env python
"""
StegVerse State Engine v0 (SCW)

Lightweight event logger for repo state, starting with:
- Workflows First-Aid summary → structured events

Usage from a workflow step, for example:

  python scripts/state_engine.py first-aid \
    --summary-path ".github/autopatch_out/FIRST_AID_SUMMARY.json"

This will append JSONL events to: .steg/state/events.jsonl
"""

import argparse
import datetime as _dt
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

# Root for all state logs in this repo
STATE_ROOT = Path(".steg") / "state"
EVENT_LOG = STATE_ROOT / "events.jsonl"


def _iso_now() -> str:
    """UTC timestamp in ISO-8601 with Z suffix."""
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _checksum(path: Path) -> Optional[str]:
    """Return SHA-256 hex digest of a file, or None if it doesn't exist."""
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except FileNotFoundError:
        return None


def _base_context() -> Dict[str, Any]:
    """Capture useful GitHub context from env for provenance."""
    env = os.environ
    return {
        "repo": env.get("GITHUB_REPOSITORY"),
        "workflow": env.get("GITHUB_WORKFLOW"),
        "run_id": env.get("GITHUB_RUN_ID"),
        "run_attempt": env.get("GITHUB_RUN_ATTEMPT"),
        "job": env.get("GITHUB_JOB"),
        "actor": env.get("GITHUB_ACTOR"),
        "ref": env.get("GITHUB_REF"),
        "ref_name": env.get("GITHUB_REF_NAME"),
        "sha": env.get("GITHUB_SHA"),
    }


def _write_event(event: Dict[str, Any]) -> None:
    """Append one event as JSON to the global event log."""
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    with EVENT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=False) + "\n")


# ---------- Mode: first-aid → record FIRST_AID_SUMMARY.json ----------

def _load_first_aid_summary(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"FIRST_AID summary not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _cmd_first_aid(summary_path: str) -> None:
    """
    Record events derived from FIRST_AID_SUMMARY.json, produced by
    Workflows First-Aid Sweep.
    """
    summary_file = Path(summary_path)
    data = _load_first_aid_summary(summary_file)

    fixed: List[str] = data.get("fixed", []) or []
    added_dispatch: List[str] = data.get("added_dispatch", []) or []
    still_broken: List[Tuple[str, str]] = data.get("still_broken", []) or []

    ctx = _base_context()
    now = _iso_now()

    # For quick lookup
    added_dispatch_set = set(added_dispatch)
    fixed_set = set(fixed)

    # 1) Log fixed workflows
    for name in fixed:
        wf_rel = Path(".github") / "workflows" / name
        event = {
            "ts": now,
            "namespace": "SCW",
            "kind": "workflow_first_aid",
            "event_type": "repair",
            "status": "fixed",
            "resource_type": "workflow",
            "resource_name": name,
            "path": str(wf_rel),
            "post_checksum": _checksum(wf_rel),
            "labels": [
                "first_aid",
                "repair",
                "dispatch_injected" if name in added_dispatch_set else "no_dispatch_change",
            ],
            "meta": ctx,
        }
        _write_event(event)

    # 2) Log cases where we injected dispatch but they weren't in "fixed"
    #    (defensive: future versions might separate them)
    for name in added_dispatch_set - fixed_set:
        wf_rel = Path(".github") / "workflows" / name
        event = {
            "ts": now,
            "namespace": "SCW",
            "kind": "workflow_first_aid",
            "event_type": "repair",
            "status": "dispatch_added_only",
            "resource_type": "workflow",
            "resource_name": name,
            "path": str(wf_rel),
            "post_checksum": _checksum(wf_rel),
            "labels": [
                "first_aid",
                "dispatch_only",
            ],
            "meta": ctx,
        }
        _write_event(event)

    # 3) Log still-broken workflows with error types
    for item in still_broken:
        # Expect ["filename.yml", "ErrorType"]
        if not item:
            continue
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            name, err_type = item[0], item[1]
        else:
            # fallback if shape is weird
            name = str(item)
            err_type = "UnknownError"

        wf_rel = Path(".github") / "workflows" / name
        event = {
            "ts": now,
            "namespace": "SCW",
            "kind": "workflow_first_aid",
            "event_type": "repair",
            "status": "still_broken",
            "error_type": err_type,
            "resource_type": "workflow",
            "resource_name": name,
            "path": str(wf_rel),
            "post_checksum": _checksum(wf_rel),
            "labels": [
                "first_aid",
                "broken",
            ],
            "meta": ctx,
        }
        _write_event(event)


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        description="StegVerse State Engine v0 (SCW) – event logger"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: first-aid
    p_first = subparsers.add_parser(
        "first-aid",
        help="Record events from FIRST_AID_SUMMARY.json (Workflows First-Aid Sweep).",
    )
    p_first.add_argument(
        "--summary-path",
        required=True,
        help="Path to FIRST_AID_SUMMARY.json (e.g. .github/autopatch_out/FIRST_AID_SUMMARY.json)",
    )

    args = parser.parse_args(argv)

    if args.command == "first-aid":
        _cmd_first_aid(args.summary_path)
        return 0

    # Fallback; should never hit here because of required=True
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
