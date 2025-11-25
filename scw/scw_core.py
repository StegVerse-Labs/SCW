#!/usr/bin/env python3
"""
SCW Core v3 (safe)
- Commands: self-test, autopatch
- Requires env GH_TOKEN (mapped from org/repo secret).
- Safe-by-default with dry_run support.
"""

import argparse
import datetime as _dt
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional, Tuple, List

import requests


# --------------------------
# Helpers
# --------------------------

def log(msg: str):
    print(msg, flush=True)


def die(msg: str, code: int = 1):
    log(f"[SCW] ERROR: {msg}")
    sys.exit(code)


def run(cmd: List[str], cwd: Optional[str] = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a subprocess, streaming output."""
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, capture_output=False)


def sh(cmd: List[str], cwd: Optional[str] = None) -> str:
    """Run a subprocess and return stdout."""
    p = subprocess.run(cmd, cwd=cwd, check=True, text=True, capture_output=True)
    return (p.stdout or "").strip()


def now_stamp() -> str:
    return _dt.datetime.utcnow().strftime("%Y%m%d-%H%M%S")


def parse_repo(full_name: str) -> Tuple[str, str]:
    if not full_name or "/" not in full_name:
        raise ValueError("target_repo must be like ORG/REPO")
    org, repo = full_name.split("/", 1)
    return org.strip(), repo.strip()


def gh_api_headers(token: str) -> dict:
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "SCW-Core"
    }


def get_env_token() -> str:
    # Primary mapping from workflow:
    # env:
    #   GH_TOKEN: ${{ secrets.GH_STEGVERSE_LABS_AI_TOKEN || secrets.GH_STEGVERSE_AI_TOKEN }}
    tok = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN") or ""
    tok = tok.strip()
    if not tok:
        die("No GitHub token found. Ensure org/repo secret GH_STEGVERSE_*_AI_TOKEN exists and workflow maps it to env GH_TOKEN.")
    return tok


def make_authed_url(target_repo: str, token: str) -> str:
    """
    Build a PAT-auth URL for pushing.
    We DO NOT print it anywhere.
    """
    org, repo = parse_repo(target_repo)
    return f"https://x-access-token:{token}@github.com/{org}/{repo}.git"


def gh_get(url: str, token: str):
    r = requests.get(url, headers=gh_api_headers(token), timeout=30)
    if r.status_code >= 300:
        raise RuntimeError(f"GET {url} failed: {r.status_code} {r.text[:200]}")
    return r.json()


def gh_post(url: str, token: str, payload: dict):
    r = requests.post(url, headers=gh_api_headers(token), json=payload, timeout=30)
    if r.status_code >= 300:
        raise RuntimeError(f"POST {url} failed: {r.status_code} {r.text[:200]}")
    return r.json()


def list_org_repos(org: str, token: str, per_page: int = 100, max_pages: int = 5) -> List[str]:
    repos = []
    for page in range(1, max_pages + 1):
        url = f"https://api.github.com/orgs/{org}/repos?per_page={per_page}&page={page}"
        data = gh_get(url, token)
        if not data:
            break
        repos.extend([d["full_name"] for d in data if "full_name" in d])
    return repos


def default_base_branch(token: str, target_repo: str) -> str:
    org, repo = parse_repo(target_repo)
    url = f"https://api.github.com/repos/{org}/{repo}"
    data = gh_get(url, token)
    return data.get("default_branch", "main")


# --------------------------
# Commands
# --------------------------

@dataclass
class Args:
    command: str
    target_repo: str
    org: Optional[str]
    base_branch: Optional[str]
    dry_run: bool
    patch_message: str


def cmd_self_test(args: Args, token: str):
    org = args.org or parse_repo(args.target_repo)[0]

    log(f"[SCW] Command: self-test")
    log(f"[SCW] Target repo: {args.target_repo}")
    log(f"[SCW] Org: {org}")

    # token auth check
    me = gh_get("https://api.github.com/user", token)
    login = me.get("login", "unknown")
    log(f"[SCW] Token check OK. Auth login: {login}")

    repos = list_org_repos(org, token)
    log(f"[SCW] Token can see {len(repos)} repos in {org}.")
    if repos:
        sample = ", ".join(repos[:10])
        log(f"[SCW] Sample repos: {sample}")

    log("[SCW] Self-test PASS.")


def cmd_autopatch(args: Args, token: str):
    log(f"[SCW] Command: autopatch")
    log(f"[SCW] Target repo: {args.target_repo}")
    log(f"[SCW] Dry run: {args.dry_run}")

    base_branch = args.base_branch or default_base_branch(token, args.target_repo)
    log(f"[SCW] Base branch: {base_branch}")

    # Work in a temp folder
    work = os.path.abspath("workdir")
    if os.path.exists(work):
        run(["rm", "-rf", work], check=False)
    os.makedirs(work, exist_ok=True)

    # Clone
    authed_url = make_authed_url(args.target_repo, token)
    log("[SCW] Cloning target repo...")
    run(["git", "clone", authed_url, work])

    # Checkout base
    run(["git", "checkout", base_branch], cwd=work)

    # Create branch
    branch = f"autopatch/{now_stamp()}"
    run(["git", "checkout", "-b", branch], cwd=work)

    # ---------------------------
    # Placeholder patch logic
    # ---------------------------
    # This is where your real patcher would run.
    # For safety, we only touch a tiny marker file.
    marker_path = os.path.join(work, ".scw_autopatch_marker")
    with open(marker_path, "w", encoding="utf-8") as f:
        f.write(f"autopatch generated at {now_stamp()} UTC\n")

    run(["git", "add", "-A"], cwd=work)

    # If nothing changed, bail
    status = sh(["git", "status", "--porcelain"], cwd=work)
    if not status.strip():
        log("[SCW] No changes detected. Exiting without PR.")
        return

    # Commit
    msg = args.patch_message or "SCW autopatch"
    run(["git", "commit", "-m", msg], cwd=work)

    if args.dry_run:
        log("[SCW] Dry-run enabled: skipping push + PR creation.")
        return

    # -----------------------------------------
    # PUSH FIX: ensure origin is PAT-auth URL
    # -----------------------------------------
    log("[SCW] Pushing branch with PAT-auth URL...")
    run(["git", "remote", "set-url", "origin", authed_url], cwd=work)
    run(["git", "push", "--set-upstream", "origin", branch], cwd=work)

    # Create PR
    org, repo = parse_repo(args.target_repo)
    pr_title = msg
    pr_body = "Automated autopatch generated by SCW."
    pr_payload = {
        "title": pr_title,
        "head": branch,
        "base": base_branch,
        "body": pr_body,
        "maintainer_can_modify": True,
    }

    log("[SCW] Creating PR...")
    pr = gh_post(f"https://api.github.com/repos/{org}/{repo}/pulls", token, pr_payload)
    pr_url = pr.get("html_url", "")
    log(f"[SCW] PR created: {pr_url}")


# --------------------------
# CLI
# --------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="scw_core")
    p.add_argument("command", choices=["self-test", "autopatch"], help="SCW command to run")
    p.add_argument("--target-repo", required=True, help="Target repo full name ORG/REPO")
    p.add_argument("--org", default=None, help="Org override (optional)")
    p.add_argument("--base-branch", default=None, help="Base branch override (optional)")
    p.add_argument("--dry-run", action="store_true", help="If set, do NOT push or open PR")
    p.add_argument("--patch-message", default="SCW autopatch", help="Commit/PR title")
    return p


def main():
    parser = build_parser()
    ns = parser.parse_args()

    token = get_env_token()

    args = Args(
        command=ns.command,
        target_repo=ns.target_repo,
        org=ns.org,
        base_branch=ns.base_branch,
        dry_run=bool(ns.dry_run),
        patch_message=ns.patch_message,
    )

    if args.command == "self-test":
        cmd_self_test(args, token)
    elif args.command == "autopatch":
        cmd_autopatch(args, token)
    else:
        die(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
