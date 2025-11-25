"""
SCW Core – StegVerse Continuous Workflow Engine
Supports:
  - self-test
  - autopatch
  - org-scan
"""

import os
import sys
import json
import argparse
import datetime
import subprocess
import pathlib

from .org_health import org_health_scan

# ---------------------------------------------
# Utilities
# ---------------------------------------------

def log(msg):
    print(f"[SCW] {msg}", flush=True)

def run(cmd, cwd=None, check=True):
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        text=True,
        capture_output=False
    )

def run_capture(cmd, cwd=None):
    p = subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True
    )
    return p.stdout.strip()

def ensure_token():
    token = os.getenv("GH_TOKEN")
    if not token:
        raise SystemExit("[SCW] ERROR: GH_TOKEN missing. Ensure the workflow maps an org token to GH_TOKEN.")
    return token

# ---------------------------------------------
# Commands
# ---------------------------------------------

def cmd_self_test(args, token):
    log("Command: self-test")
    log(f"Target repo: {args.target_repo}")
    log(f"Org: {args.org}")

    try:
        org_health_scan(
            org=args.org,
            target_repo=args.target_repo,
            dry_run=True,
            autofix=False
        )
    except Exception as e:
        raise SystemExit(f"[SCW] Self-test FAILED: {e}")

    log("Self-test PASS.")
    return


def cmd_autopatch(args, token):
    log("Command: autopatch")
    if not args.target_repo:
        raise SystemExit("[SCW] autopatch requires --target-repo")

    dry = args.dry_run
    repo_full = args.target_repo
    owner, repo = repo_full.split("/")
    base_branch = args.base_branch

    # --------------------------------------
    # Clone repo
    # --------------------------------------
    workdir = pathlib.Path("work") / repo
    if workdir.exists():
        run(["rm", "-rf", str(workdir)], check=False)
    workdir.mkdir(parents=True, exist_ok=True)

    log(f"Cloning {repo_full}…")
    clone_url = f"https://x-access-token:{token}@github.com/{repo_full}.git"
    run(["git", "clone", clone_url, str(workdir)])

    os.chdir(workdir)

    # Ensure we are on base branch
    run(["git", "checkout", base_branch])

    # Create autopatch branch
    ts = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    branch = f"autopatch/{ts}"
    log(f"Creating branch: {branch}")
    run(["git", "checkout", "-b", branch])

    # --------------------------------------
    # Apply SCW patch
    # (This is a placeholder marker — safe)
    # --------------------------------------
    marker = pathlib.Path("SCW_AUTOPATCH_MARKER.txt")
    marker.write_text(f"Autopatch run at {ts} UTC\n", encoding="utf-8")

    # Commit
    run(["git", "add", "-A"])
    commit_result = subprocess.run(["git", "commit", "-m", f"SCW autopatch {ts}"])
    if commit_result.returncode != 0:
        log("No changes were made — nothing to autopatch.")
        os.chdir(pathlib.Path(__file__).resolve().parents[2])
        return

    if dry:
        log("Dry-run enabled — NOT pushing or opening PR.")
        os.chdir(pathlib.Path(__file__).resolve().parents[2])
        return

    # --------------------------------------
    # Push with PAT-auth
    # --------------------------------------
    log("Pushing branch...")
    run(["git", "push", "--set-upstream", "origin", branch])

    # --------------------------------------
    # Create PR
    # --------------------------------------
    import requests
    pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
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
    r = requests.post(pr_url, headers=headers, json=body)
    if r.status_code >= 300:
        raise SystemExit(f"[SCW] Failed to open PR: {r.text}")

    url = r.json().get("html_url", "")
    log(f"Autopatch PR created: {url}")

    os.chdir(pathlib.Path(__file__).resolve().parents[2])
    return


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

    log("org-scan completed successfully.")
    return


# ---------------------------------------------
# Main Entrypoint
# ---------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="StegVerse SCW Core Engine")

    parser.add_argument(
        "command",
        choices=["self-test", "autopatch", "org-scan"]
    )

    parser.add_argument("--org", default="StegVerse-Labs")
    parser.add_argument("--target-repo", default="")
    parser.add_argument("--dry-run", default="false")
    parser.add_argument("--base-branch", default="main")

    args = parser.parse_args()

    # Normalize dry-run
    if isinstance(args.dry_run, str):
        args.dry_run = args.dry_run.lower() == "true"

    token = ensure_token()

    if args.command == "self-test":
        return cmd_self_test(args, token)
    if args.command == "autopatch":
        return cmd_autopatch(args, token)
    if args.command == "org-scan":
        return cmd_org_scan(args, token)

    raise SystemExit(f"[SCW] Unknown command: {args.command}")


if __name__ == "__main__":
    main()
