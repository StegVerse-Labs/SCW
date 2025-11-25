"""
SCW Core – StegVerse Continuous Workflow Engine
Supports:
  - self-test
  - autopatch
  - org-scan (new)
"""

import os
import sys
import json
import argparse
import datetime
import subprocess
import pathlib
from typing import Optional

from .org_health import org_health_scan

# ---------------------------------------------
# Utilities
# ---------------------------------------------

def log(msg):
    print(f"[SCW] {msg}")

def run(cmd, cwd=None, check=True):
    """Run a subprocess with consistent flags."""
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        text=True,
        capture_output=False
    )

def ensure_token():
    token = os.getenv("GH_TOKEN")
    if not token:
        raise SystemExit("[SCW] ERROR: No GH_TOKEN found. Workflow must map a token to env GH_TOKEN.")
    return token

def clone_repo(repo_full: str) -> pathlib.Path:
    """Clone a repo into a temporary work directory and return the path."""
    owner, repo = repo_full.split("/")
    workdir = pathlib.Path("work") / repo
    if workdir.exists():
        subprocess.run(["rm", "-rf", str(workdir)], check=True)
    workdir.mkdir(parents=True, exist_ok=True)

    log(f"Cloning {repo_full}…")
    run(["git", "clone", f"https://github.com/{repo_full}.git", str(workdir)])
    return workdir

def commit_all(msg: str) -> bool:
    """Attempt git commit. If no changes, commit exits 1 — swallow it."""
    subprocess.run(["git", "add", "-A"], check=True)
    p = subprocess.run(["git", "commit", "-m", msg])
    return p.returncode == 0

# ---------------------------------------------
# Commands
# ---------------------------------------------

def cmd_self_test(args, token):
    log("Command: self-test")
    log(f"Target repo: {args.target_repo}")
    log(f"Org: {args.org}")

    # This is intentionally simple: validate we can auth and see repos
    try:
        # call org scan with dry_run = True but only for the single repo
        result = org_health_scan(
            org=args.org,
            target_repo=args.target_repo,
            dry_run=True,
            autofix=False
        )
    except Exception as e:
        log(f"Self-test FAILED: {e}")
        raise

    log("Self-test PASS.")
    return

def cmd_autopatch(args, token):
    log("Command: autopatch")
    repo_full = args.target_repo
    org = args.org
    dry = args.dry_run
    base_branch = args.base_branch

    if not repo_full:
        raise SystemExit("[SCW] autopatch requires --target-repo")

    workdir = clone_repo(repo_full)
    os.chdir(workdir)

    ts = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    branch = f"autopatch/{ts}"

    # Create branch safely
    run(["git", "checkout", "-B", branch])

    # Example autopatch: add a timestamp marker file (placeholder)
    pathlib.Path("SCW_AUTOPATCH_MARKER.txt").write_text(
        f"Autopatch performed at {ts} UTC\n",
        encoding="utf-8"
    )

    changed = commit_all(f"SCW autopatch {ts}")

    if not changed:
        log("No changes detected — autopatch produced nothing.")
        os.chdir(pathlib.Path(__file__).resolve().parents[2])
        return

    if dry:
        log("Dry-run mode: NOT pushing branch or opening PR.")
        os.chdir(pathlib.Path(__file__).resolve().parents[2])
        return

    # Push & PR
    log("Pushing branch with PAT-auth URL...")
    try:
        run(["git", "push", "--set-upstream", "origin", branch])
    except Exception as e:
        log(f"Push failed: {e}")
        os.chdir(pathlib.Path(__file__).resolve().parents[2])
        raise

    # Open PR
    import requests
    owner, repo = repo_full.split("/")
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    body = {
        "title": f"SCW autopatch {ts}",
        "head": branch,
        "base": base_branch,
        "body": "Automated autopatch performed by SCW."
    }
    r = requests.post(url, headers=headers, json=body)
    if r.status_code >= 300:
        raise SystemExit(f"[SCW] Failed to open PR: {r.text}")

    pr_url = r.json().get("html_url", "(unknown)")
    log(f"Autopatch PR created: {pr_url}")

    os.chdir(pathlib.Path(__file__).resolve().parents[2])

def cmd_org_scan(args, token):
    log("Command: org-scan")

    try:
        org_health_scan(
            org=args.org,
            target_repo=args.target_repo or None,
            dry_run=args.dry_run,
            autofix=(not args.dry_run)
        )
    except Exception as e:
        raise SystemExit(f"[SCW] org-scan FAILED: {e}")

    log("org-scan completed.")
    return

# ---------------------------------------------
# Main Entrypoint
# ---------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="StegVerse SCW Core Engine")
    parser.add_argument(
        "command",
        choices=["self-test", "autopatch", "org-scan"],
        help="SCW command"
    )
    parser.add_argument("--org", required=False, default="StegVerse-Labs")
    parser.add_argument("--target-repo", required=False, default="")
    parser.add_argument("--dry-run", required=False, default="false")
    parser.add_argument("--base-branch", required=False, default="main")

    args = parser.parse_args()

    # Normalize dry-run value ("true"/"false"/bool)
    if isinstance(args.dry_run, str):
        args.dry_run = args.dry_run.lower() == "true"

    token = ensure_token()

    if args.command == "self-test":
        return cmd_self_test(args, token)
    elif args.command == "autopatch":
        return cmd_autopatch(args, token)
    elif args.command == "org-scan":
        return cmd_org_scan(args, token)

    raise SystemExit(f"[SCW] Unknown command: {args.command}")

if __name__ == "__main__":
    main()
