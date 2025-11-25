# scw/org_health.py
import os, json, time, datetime, textwrap, pathlib, subprocess
import requests

API = "https://api.github.com"

REQUIRED_FILES = [
    "README.md",
    ".github/workflows/scw_orchestrator.yml",
]

# "Safe" auto-fix rules: only add stubs / workflows, never touch app logic.
SAFE_AUTOFIX = {
    "README.md": "# {repo}\n\nAutomated health stub. Replace with real README.\n",
    ".github/workflows/scw_orchestrator.yml": None,  # provided by template below
}

SCW_ORCH_TEMPLATE = """\
name: SCW Orchestrator

on:
  workflow_dispatch:
    inputs:
      command:
        description: "SCW command: self-test, autopatch, org-scan"
        required: true
        default: "self-test"
      target_repo:
        description: "Repo to operate on (e.g., StegVerse-Labs/Trumpality)"
        required: false
        default: ""
      org:
        description: "Org to scan/operate on"
        required: false
        default: "StegVerse-Labs"
      dry_run:
        description: "If true, do not push or open PRs"
        type: boolean
        required: false
        default: true
      base_branch:
        description: "Base branch for PRs"
        required: false
        default: "main"

permissions:
  contents: write
  pull-requests: write

jobs:
  scw:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          if [ -f scw/requirements.txt ]; then pip install -r scw/requirements.txt; fi
      - name: Run SCW
        env:
          GH_TOKEN: ${{ secrets.GH_STEGVERSE_LABS_AI_TOKEN || secrets.GH_STEGVERSE_AI_TOKEN || secrets.GH_TOKEN }}
        run: |
          python -m scw.scw_core \
            --org "${{ github.event.inputs.org }}" \
            --target-repo "${{ github.event.inputs.target_repo }}" \
            --dry-run "${{ github.event.inputs.dry_run }}" \
            --base-branch "${{ github.event.inputs.base_branch }}" \
            "${{ github.event.inputs.command }}"
"""

def _hdr(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "SCW-Health"
    }

def gh_get(token, path, params=None):
    r = requests.get(f"{API}{path}", headers=_hdr(token), params=params)
    r.raise_for_status()
    return r.json()

def gh_put(token, path, body):
    r = requests.put(f"{API}{path}", headers=_hdr(token), json=body)
    r.raise_for_status()
    return r.json()

def gh_post(token, path, body):
    r = requests.post(f"{API}{path}", headers=_hdr(token), json=body)
    r.raise_for_status()
    return r.json()

def list_repos(token, org):
    repos = []
    page = 1
    while True:
        batch = gh_get(token, f"/orgs/{org}/repos", params={"per_page": 100, "page": page})
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos

def file_exists(token, owner, repo, path):
    try:
        gh_get(token, f"/repos/{owner}/{repo}/contents/{path}")
        return True
    except Exception:
        return False

def get_default_branch(token, owner, repo):
    info = gh_get(token, f"/repos/{owner}/{repo}")
    return info.get("default_branch", "main")

def ensure_branch_checkout(repo_url, branch):
    subprocess.run(["git", "checkout", "-B", branch], check=True)

def commit_all(msg):
    subprocess.run(["git", "add", "-A"], check=True)
    # if no changes, git commit exits 1; swallow
    p = subprocess.run(["git", "commit", "-m", msg])
    return p.returncode == 0

def push_branch(branch):
    subprocess.run(["git", "push", "--set-upstream", "origin", branch], check=True)

def open_pr(token, owner, repo, branch, base, title, body):
    return gh_post(token, f"/repos/{owner}/{repo}/pulls", {
        "title": title,
        "head": branch,
        "base": base,
        "body": body
    })

def scan_repo(token, full_name, dry_run=False, autofix=False):
    owner, repo = full_name.split("/")
    default_branch = get_default_branch(token, owner, repo)

    missing = []
    for path in REQUIRED_FILES:
        if not file_exists(token, owner, repo, path):
            missing.append(path)

    return {
        "repo": full_name,
        "default_branch": default_branch,
        "missing_files": missing,
    }

def apply_safe_autofix(token, repo_full, report, dry_run=False):
    owner, repo = repo_full.split("/")
    if not report["missing_files"]:
        return None

    # clone and patch locally
    repo_url = f"https://github.com/{repo_full}.git"
    workdir = pathlib.Path("work") / repo
    if workdir.exists():
        subprocess.run(["rm", "-rf", str(workdir)], check=True)
    workdir.mkdir(parents=True, exist_ok=True)

    subprocess.run(["git", "clone", repo_url, str(workdir)], check=True)
    os.chdir(workdir)

    ts = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    branch = f"healthfix/{ts}"
    ensure_branch_checkout(repo_url, branch)

    changed = False
    for path in report["missing_files"]:
        content = SAFE_AUTOFIX.get(path)
        if content is None and path.endswith("scw_orchestrator.yml"):
            content = SCW_ORCH_TEMPLATE
        if content:
            pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
            pathlib.Path(path).write_text(content.format(repo=repo), encoding="utf-8")
            changed = True

    pr_url = None
    if changed and commit_all("SCW health autofix (safe)") and not dry_run:
        push_branch(branch)
        pr = open_pr(
            token, owner, repo, branch, report["default_branch"],
            "SCW health autofix (safe)",
            "Auto-generated safe fixes: missing READMEs / SCW workflow stubs."
        )
        pr_url = pr.get("html_url")

    os.chdir(pathlib.Path(__file__).resolve().parents[2])
    return pr_url

def org_health_scan(org, target_repo=None, dry_run=False, autofix=False):
    token = os.getenv("GH_TOKEN")
    if not token:
        raise SystemExit("[SCW] ERROR: GH_TOKEN required for org-scan")

    repos = list_repos(token, org)
    repos = [r["full_name"] for r in repos]

    if target_repo:
        repos = [target_repo] if target_repo in repos else [target_repo]

    reports = []
    prs = []

    for full in repos:
        rep = scan_repo(token, full, dry_run=dry_run, autofix=autofix)
        reports.append(rep)

        if autofix and rep["missing_files"]:
            pr_url = apply_safe_autofix(token, full, rep, dry_run=dry_run)
            if pr_url:
                prs.append({"repo": full, "pr": pr_url})

    out = {
        "org": org,
        "generated_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "target_repo": target_repo,
        "dry_run": dry_run,
        "autofix": autofix,
        "reports": reports,
        "prs": prs,
    }

    pathlib.Path("reports").mkdir(exist_ok=True)
    stamp = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    path = pathlib.Path("reports") / f"org_health_{stamp}.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(json.dumps(out, indent=2))
    print(f"[SCW] Wrote report: {path}")
    return out
