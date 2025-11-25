#!/usr/bin/env python3
"""
StegVerse SCW Core v3
- self-test: validate GH_TOKEN, list visible repos in org
- autopatch: apply minimal StegVerse repo hygiene and open PR
Safety guards:
  * requires explicit "autopatch" command
  * optional allowlist
  * dry-run supported (default false at workflow level, but recommend true for first runs)
  * checks push permissions before pushing
"""

import argparse, os, sys, json, time, pathlib, subprocess, textwrap
from datetime import datetime, timezone
import requests

API = "https://api.github.com"

SECURITY_MD = """\
# Security Policy

This is a StegVerse repository.

## Reporting a Vulnerability
Please open a private security advisory or email the StegVerse maintainers
with a clear description and reproduction steps.

We aim to respond within 72 hours.
"""

STEGVERSE_MODULE_JSON = {
  "name": "",
  "description": "StegVerse module",
  "version": "0.0.1",
  "stegverse": {
    "module": True,
    "scw_managed": True,
    "last_autopatch": ""
  }
}

SCW_BRIDGE_REPO_YML = """\
name: StegVerse AI Entity (Bridge)

on:
  workflow_dispatch:
    inputs:
      instructions:
        description: "Optional instructions for StegVerse-AI-001"
        required: false

permissions:
  contents: read
  pull-requests: write

jobs:
  bridge:
    runs-on: ubuntu-latest
    steps:
      - name: Placeholder
        run: echo "Bridge workflow installed by SCW."
"""

def eprint(*a):
    print(*a, file=sys.stderr)

def get_token():
    tok = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    return tok.strip()

def gh_api(path, token, method="GET", data=None):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "StegVerse-SCW"
    }
    url = path if path.startswith("http") else f"{API}{path}"
    r = requests.request(method, url, headers=headers, json=data)
    if r.status_code >= 400:
        raise requests.HTTPError(f"{method} {url} -> {r.status_code}: {r.text}", response=r)
    return r

def parse_allowlist(s):
    if not s: return None
    items = [x.strip() for x in s.split(",") if x.strip()]
    return set(items) if items else None

def cmd_self_test(args, token):
    org = args.org
    # List repos visible to token
    repos = []
    page = 1
    while True:
        r = gh_api(f"/orgs/{org}/repos?per_page=100&page={page}", token)
        batch = r.json()
        if not batch: break
        repos.extend(batch)
        page += 1
    print(f"[SCW] Token check OK. Auth login: {gh_api('/user', token).json().get('login')}")
    print(f"[SCW] Token can see {len(repos)} repos in {org}.")
    samples = ", ".join([f"{org}/{x['name']}" for x in repos[:10]])
    print(f"[SCW] Sample repos: {samples}")
    print("[SCW] Self-test PASS.")

def ensure_file(path: pathlib.Path, content: str):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return True
    return False

def run(cmd, cwd=None, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, capture_output=False)

def has_push_permission(token, full_repo):
    owner, name = full_repo.split("/", 1)
    r = gh_api(f"/repos/{owner}/{name}", token)
    perms = r.json().get("permissions") or {}
    return bool(perms.get("push") or perms.get("admin"))

def open_pr(token, full_repo, head, base, title, body):
    owner, name = full_repo.split("/", 1)
    # if PR already exists, don't fail
    try:
        prs = gh_api(f"/repos/{owner}/{name}/pulls?state=open&head={owner}:{head}", token).json()
        if prs:
            print(f"[SCW] PR already open: {prs[0].get('html_url')}")
            return
    except Exception:
        pass
    data = {"title": title, "head": head, "base": base, "body": body}
    pr = gh_api(f"/repos/{owner}/{name}/pulls", token, method="POST", data=data).json()
    print(f"[SCW] Opened PR: {pr.get('html_url')}")

def cmd_autopatch(args, token):
    full_repo = args.target_repo
    allowlist = parse_allowlist(args.allowlist)
    if allowlist and full_repo not in allowlist and full_repo.split("/",1)[1] not in allowlist:
        print(f"[SCW] SAFETY STOP: {full_repo} not in allowlist. Skipping.")
        return

    if args.dry_run.lower() == "true":
        dry_run = True
    else:
        dry_run = False

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    branch = f"autopatch/{ts}"

    work = pathlib.Path("/tmp/scw_work")
    if work.exists():
        run(["rm","-rf",str(work)])
    work.mkdir(parents=True, exist_ok=True)

    authed_url = f"https://{token}:x-oauth-basic@github.com/{full_repo}.git"

    print(f"[SCW] Cloning {full_repo}...")
    run(["git","clone",authed_url,str(work)])
    run(["git","checkout","-b",branch], cwd=work)

    changed = False
    changed |= ensure_file(work/"SECURITY.md", SECURITY_MD)
    # module json
    mod_path = work/"stegverse-module.json"
    if not mod_path.exists():
        d = dict(STEGVERSE_MODULE_JSON)
        d["name"] = full_repo.split("/",1)[1]
        d["stegverse"]["last_autopatch"] = ts
        mod_path.write_text(json.dumps(d, indent=2), encoding="utf-8")
        changed = True
    else:
        try:
            d = json.loads(mod_path.read_text(encoding="utf-8"))
        except Exception:
            d = dict(STEGVERSE_MODULE_JSON)
        d.setdefault("stegverse", {})
        d["stegverse"]["last_autopatch"] = ts
        mod_path.write_text(json.dumps(d, indent=2), encoding="utf-8")
        changed = True

    bridge_path = work/".github"/"workflows"/"scw_bridge_repo.yml"
    if not bridge_path.exists():
        bridge_path.parent.mkdir(parents=True, exist_ok=True)
        bridge_path.write_text(SCW_BRIDGE_REPO_YML, encoding="utf-8")
        changed = True

    if not changed:
        print("[SCW] No changes needed; exiting.")
        return

    run(["git","add","-A"], cwd=work)
    run(["git","config","user.name","StegVerse-AI"], cwd=work)
    run(["git","config","user.email","stegverse-ai@users.noreply.github.com"], cwd=work)
    run(["git","commit","-m",f"SCW autopatch {ts}"], cwd=work)

    if dry_run:
        print("[SCW] Dry-run enabled, not pushing.")
        return

    if not has_push_permission(token, full_repo):
        print("[SCW] SAFETY STOP: Token lacks push permission to this repo. No push attempted.")
        return

    print("[SCW] Pushing branch with PAT-auth URL...")
    run(["git","push","origin",branch], cwd=work)

    title = f"SCW autopatch {ts}"
    body = "Automated StegVerse repo hygiene patch via SCW."
    open_pr(token, full_repo, branch, args.base_branch, title, body)
    print("[SCW] Autopatch complete.")

def main():
    ap = argparse.ArgumentParser(prog="scw_core")
    ap.add_argument("--org", default=None)
    ap.add_argument("--target-repo", required=True)
    ap.add_argument("--base-branch", default="main")
    ap.add_argument("--dry-run", default="false")
    ap.add_argument("--allowlist", default="")
    ap.add_argument("command", choices=["self-test","autopatch"])
    args = ap.parse_args()

    token = get_token()
    if not token:
        print("[SCW] ERROR: No GitHub token found. Ensure GH_TOKEN env is set.")
        sys.exit(1)

    if not args.org:
        args.org = args.target_repo.split("/",1)[0]

    if args.command == "self-test":
        cmd_self_test(args, token)
    else:
        cmd_autopatch(args, token)

if __name__ == "__main__":
    main()
