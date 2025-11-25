#!/usr/bin/env python
"""
StegVerse State Engine Reader v0 (SCW)

Reads .steg/state/events.jsonl (written by state_engine.py) and
produces:

- A human-friendly Markdown snapshot of workflow state:
    .github/docs/STATE_SNAPSHOT.md

- A machine-readable JSON index of the latest event per workflow:
    .steg/state/latest_per_workflow.json

Current focus:
- namespace = "SCW"
- kind      = "workflow_first_aid"
"""

import argparse
import datetime as _dt
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def _iso_now() -> str:
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _load_events(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    events: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                events.append(obj)
    return events


def _filter_scw_workflow_events(
    events: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for ev in events:
        if ev.get("namespace") != "SCW":
            continue
        if ev.get("kind") != "workflow_first_aid":
            continue
        out.append(ev)
    return out


def _parse_ts(ts: Optional[str]) -> str:
    """
    For now we just return the timestamp string, but we rely on
    ISO-8601 ordering (lexicographic ~ chronological).
    """
    return ts or ""


def _build_latest_by_workflow(
    events: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Returns a dict: workflow_name -> latest_event
    """
    latest: Dict[str, Dict[str, Any]] = {}
    for ev in events:
        name = ev.get("resource_name")
        if not name:
            continue
        ts = _parse_ts(ev.get("ts"))

        existing = latest.get(name)
        if existing is None:
            latest[name] = ev
            continue

        old_ts = _parse_ts(existing.get("ts"))
        if ts > old_ts:
            latest[name] = ev
    return latest


def _summarize_status(ev: Dict[str, Any]) -> str:
    status = ev.get("status") or "unknown"
    err_type = ev.get("error_type")
    if status == "fixed":
        return "✅ fixed"
    if status == "dispatch_added_only":
        return "⚪ dispatch-only"
    if status == "still_broken":
        if err_type:
            return f"❌ still_broken · `{err_type}`"
        return "❌ still_broken"
    return f"ℹ️ {status}"


def _status_bucket(ev: Dict[str, Any]) -> str:
    status = ev.get("status") or "unknown"
    if status == "fixed":
        return "fixed"
    if status == "still_broken":
        return "broken"
    if status == "dispatch_added_only":
        return "dispatch_only"
    return "other"


def _render_markdown(
    latest: Dict[str, Dict[str, Any]]
) -> str:
    # Aggregate stats
    fixed = broken = dispatch_only = other = 0
    for ev in latest.values():
        bucket = _status_bucket(ev)
        if bucket == "fixed":
            fixed += 1
        elif bucket == "broken":
            broken += 1
        elif bucket == "dispatch_only":
            dispatch_only += 1
        else:
            other += 1

    total = len(latest)
    now = _iso_now()

    lines: List[str] = []
    lines.append("# StegVerse State Snapshot (SCW)")
    lines.append("")
    lines.append(f"_Generated: **{now}**_")
    lines.append("")
    lines.append(f"- ✅ Fixed workflows: **{fixed}**")
    lines.append(f"- ❌ Still broken: **{broken}**")
    lines.append(f"- ⚪ Dispatch-only entries: **{dispatch_only}**")
    lines.append(f"- ℹ️ Other states: **{other}**")
    lines.append(f"- Total tracked workflows: **{total}**")
    lines.append("")

    if total == 0:
        lines.append("> No SCW workflow events recorded yet in `.steg/state/events.jsonl`.")
        lines.append("")
        return "\n".join(lines)

    lines.append("| Workflow | Last status | Last checksum | Labels | Last run ID | Last ts |")
    lines.append("|---|---|---|---|---|---|")

    for name in sorted(latest.keys()):
        ev = latest[name]
        status_str = _summarize_status(ev)
        checksum = ev.get("post_checksum") or ""
        labels = ev.get("labels") or []
        labels_str = ", ".join(str(x) for x in labels)
        meta = ev.get("meta") or {}
        run_id = meta.get("run_id") or ""
        ts = ev.get("ts") or ""
        lines.append(
            f"| `{name}` | {status_str} | `{checksum}` | {labels_str} | `{run_id}` | `{ts}` |"
        )

    lines.append("")
    lines.append("> Source: `.steg/state/events.jsonl` (StegVerse State Engine v0).")
    lines.append("")

    return "\n".join(lines)


def _build_latest_json(
    latest: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Build a compact JSON index keyed by workflow name.

    This is designed specifically so future AI entities can consume
    state without re-parsing the entire events log.
    """
    index: Dict[str, Any] = {}
    for name, ev in latest.items():
        index[name] = {
            "status": ev.get("status"),
            "error_type": ev.get("error_type"),
            "post_checksum": ev.get("post_checksum"),
            "labels": ev.get("labels") or [],
            "namespace": ev.get("namespace"),
            "kind": ev.get("kind"),
            "ts": ev.get("ts"),
            "meta": ev.get("meta") or {},
        }
    return index


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(
        description="StegVerse State Engine Reader v0 (SCW) – snapshot generator"
    )
    parser.add_argument(
        "mode",
        choices=["snapshot"],
        help="Reader mode. Currently only 'snapshot' is implemented.",
    )
    parser.add_argument(
        "--events-path",
        default=".steg/state/events.jsonl",
        help="Path to events log (default: .steg/state/events.jsonl)",
    )
    parser.add_argument(
        "--output",
        default=".github/docs/STATE_SNAPSHOT.md",
        help="Output Markdown path (default: .github/docs/STATE_SNAPSHOT.md)",
    )
    parser.add_argument(
        "--latest-json",
        default=".steg/state/latest_per_workflow.json",
        help="Output JSON index path (default: .steg/state/latest_per_workflow.json)",
    )

    args = parser.parse_args(argv)

    events_path = Path(args.events_path)
    output_path = Path(args.output)
    latest_json_path = Path(args.latest_json)

    events = _load_events(events_path)
    scw_events = _filter_scw_workflow_events(events)
    latest = _build_latest_by_workflow(scw_events)

    # Markdown snapshot
    markdown = _render_markdown(latest)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")

    # JSON index
    latest_json_path.parent.mkdir(parents=True, exist_ok=True)
    latest_index = _build_latest_json(latest)
    latest_json_path.write_text(
        json.dumps(latest_index, indent=2),
        encoding="utf-8",
    )

    print(f"Wrote state snapshot to: {output_path}")
    print(f"Wrote latest index to:   {latest_json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
