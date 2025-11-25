#!/usr/bin/env python3
"""
StegVerse — Sovereign Control Workspace (SCW) core orchestrator.

v2 fixes:
- requirements.txt exists at scw/requirements.txt
- CLI supports env fallbacks so workflows don't hard-fail on missing inputs
- clearer error messages around GH_TOKEN
"""

from __future__ import annotations
import argparse, os, subprocess, sys, json, datetime, pathlib, textwrap
from typing import Optional, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[1]

def eprint(*a):
    print(*a, file=sys.stderr)

def get_env(name: str, default: Optional[str]=None) -> Optional[str]:
    v = os.getenv(name)
    return v if v not in (None, "") else default

def gh_token() -> Optional[str]:
    """Return a GitHub token from common env names.

    Priority:
      1) GH_TOKEN (preferred)
      2) GH_STEGVERSE_AI_TOKEN / GH_STEGVERSE_PAT / PAT_WORKFLOW_FG / PAT_WORKFLOW (legacy SCW names)
      3) GITHUB_TOKEN (GitHub Actions default)
    """
    for name in [
        "GH_TOKEN",
        "GH_STEGVERSE_AI_TOKEN",
        "GH_STEGVERSE_PAT",
        "PAT_WORKFLOW_FG",
        "PAT_WORKFLOW",
        "GITHUB_TOKEN",
    ]:
        tok = get_env(name)
        if tok:
            return tok
    return None

def run(cmd, cwd=None, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, capture_output=False)

def gh_can_access(token: str, org: str) -> Tuple[bool, str]:
    """Lightweight check by calling `gh api` if available, else skip."""
    try:
        r = subprocess.run(
            ["gh", "api", "user", "-H", f"Authorization: token {token}"],
            text=True, capture_output=True, check=False
        )
        if r.returncode == 0:
            login = json.loads(r.stdout or "{}").get("login", "")
            return True, login
        return False, (r.stderr or "").strip()
    except FileNotFoundError:
        return True, "gh-not-installed"

def cmd_self_test(org: str, target_repo: str):
    print(f"[SCW] Command: self-test")
    print(f"[SCW] Target repo: {target_repo}")
    tok = gh_token()
    if not tok:
        eprint("[SCW] ERROR: No GitHub token found.")
        eprint("[SCW] Ensure org/repo secret GH_STEGVERSE_AI_TOKEN exists and workflow maps it to env GH_TOKEN.")
        sys.exit(1)

    ok, who = gh_can_access(tok, org)
    if ok:
        print(f"[SCW] Token check OK. Auth login: {who}")
    else:
        eprint(f"[SCW] WARNING: token check failed: {who}")

    # best-effort list repos visible to token
    try:
        r = subprocess.run(
            ["gh", "repo", "list", org, "--limit", "50", "--json", "nameWithOwner"],
            text=True, capture_output=True, check=False,
            env={**os.environ, "GH_TOKEN": tok}
        )
        if r.returncode == 0:
            data = json.loads(r.stdout or "[]")
            print(f"[SCW] Token can see {len(data)} repos in {org}.")
            if data:
                samples = ", ".join([d["nameWithOwner"] for d in data[:10]])
                print(f"[SCW] Sample repos: {samples}")
        else:
            print(f"[SCW] Repo list skipped: gh returned {r.returncode}")
    except FileNotFoundError:
        print("[SCW] gh CLI not installed in runner; skipping repo list.")

    print("[SCW] Self-test PASS.")

def ensure_git_identity():
    # GitHub Actions sometimes has empty ident; set safe defaults
    name = get_env("GIT_AUTHOR_NAME", "StegVerse-AI")
    email = get_env("GIT_AUTHOR_EMAIL", "stegverse-ai@users.noreply.github.com")
    run(["git", "config", "--global", "user.name", name], check=False)
    run(["git", "config", "--global", "user.email", email], check=False)

def cmd_autopatch(org: str, target_repo: str, base_branch: str="main"):
    # Safety preflight
    tok = gh_token()
    if not tok:
        eprint("[SCW] ERROR: No GitHub token found. Set org secret GH_STEGVERSE_AI_TOKEN (or GH_TOKEN) and pass it as env GH_TOKEN.")
        return 1
    ok, who = gh_can_access(tok, org)
    if not ok:
        eprint(f"[SCW] ERROR: Token check failed: {who}")
        return 1

    """
    Clone target repo, add standard files if missing, commit to a new branch,
    push, and open a PR.
    """
    tok = gh_token()
    if not tok:
        eprint("[SCW] ERROR: No GitHub token found for autopatch.")
        sys.exit(1)

    ensure_git_identity()

    work = pathlib.Path("/tmp/scw-autopatch")
    if work.exists():
        subprocess.run(["rm", "-rf", str(work)])
    work.mkdir(parents=True, exist_ok=True)

    url = f"https://github.com/{target_repo}.git"
    print(f"[SCW] Cloning {url}")
    run(["git", "clone", "--depth", "1", "--branch", base_branch, url, str(work)])

    # Example standard files
    std_files = {
        "SECURITY.md": textwrap.dedent("""\
            # Security Policy
            Please report security issues privately to the StegVerse maintainers.
            """),
        "stegverse-module.json": json.dumps({
            "name": target_repo.split("/")[-1],
            "org": org,
            "managedBy": "SCW",
            "version": "0.0.0",
        }, indent=2) + "\n",
    }

    changed = False
    for rel, content in std_files.items():
        p = work / rel
        if not p.exists():
            p.write_text(content, encoding="utf-8")
            changed = True

    if not changed:
        print("[SCW] Nothing to patch; exiting cleanly.")
        return

    branch = f"autopatch/{datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    run(["git", "checkout", "-b", branch], cwd=work)
    run(["git", "add", "."], cwd=work)
    run(["git", "commit", "-m", "chore(autopatch): add missing StegVerse standard files"], cwd=work)

    authed_push_url = f"https://x-access-token:{tok}@github.com/{target_repo}.git"
    print("[SCW] Pushing branch with PAT-auth URL...")
    run(["git", "push", authed_push_url, branch], cwd=work)

    # Open PR via gh if available
    try:
        pr = subprocess.run(
            ["gh", "pr", "create", "--repo", target_repo, "--base", base_branch, "--head", branch,
             "--title", "chore(autopatch): standard files", "--body", "SCW autopatch"],
            text=True, capture_output=True, check=False,
            env={**os.environ, "GH_TOKEN": tok}
        )
        if pr.returncode == 0:
            print(pr.stdout.strip())
        else:
            print("[SCW] PR create skipped or failed; you can open manually.")
            print(pr.stderr.strip())
    except FileNotFoundError:
        print("[SCW] gh CLI not installed; open PR manually.")

def build_parser():
    p = argparse.ArgumentParser(prog="scw_core", description="StegVerse SCW core")
    p.add_argument("command", nargs="?", choices=["self-test", "autopatch"],
                   help="Command to run")
    p.add_argument("--org", default=None, help="GitHub org name")
    p.add_argument("--target-repo", default=None, help="Full repo name ORG/REPO")
    p.add_argument("--base-branch", default="main", help="Default branch to target")

    return p

def main():
    parser = build_parser()
    args, _ = parser.parse_known_args()

    # v2 env fallbacks
    cmd = args.command or get_env("SCW_COMMAND")
    org = args.org or get_env("ORG_GITHUB") or get_env("SCW_ORG") or "StegVerse-Labs"
    target_repo = args.target_repo or get_env("TARGET_REPO") or get_env("SCW_TARGET_REPO")

    if not cmd or not target_repo:
        eprint("[SCW] ERROR: command and --target-repo are required.")
        eprint("Usage examples:")
        eprint("  python scw/scw_core.py self-test --org StegVerse-Labs --target-repo StegVerse-Labs/TVC")
        eprint("  python scw/scw_core.py autopatch --target-repo StegVerse-Labs/TVC")
        sys.exit(2)

    if cmd == "self-test":
        cmd_self_test(org, target_repo)
    elif cmd == "autopatch":
        cmd_autopatch(org, target_repo, base_branch=args.base_branch)
    else:
        eprint(f"[SCW] Unknown command: {cmd}")
        sys.exit(2)

if __name__ == "__main__":
    main()