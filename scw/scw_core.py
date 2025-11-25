#!/usr/bin/env python3
import argparse, os, subprocess, sys, json, datetime, re, shutil, pathlib

ORG_DEFAULT = os.getenv("ORG_GITHUB", "StegVerse-Labs")
TOKEN_ENV_KEYS = ["GH_TOKEN", "GITHUB_TOKEN", "GH_STEGVERSE_AI_TOKEN"]

STANDARD_FILES = [
    "SECURITY.md",
    ".github/workflows/scw_bridge_repo.yml",
    "stegverse-module.json",
]

def die(msg, code=1):
    print(f"[SCW] ERROR: {msg}", file=sys.stderr)
    sys.exit(code)

def sh(cmd, cwd=None, capture=False):
    if capture:
        return subprocess.check_output(cmd, cwd=cwd, text=True).strip()
    print(f"[SCW] $ {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=cwd)

def get_token():
    for k in TOKEN_ENV_KEYS:
        v = os.getenv(k)
        if v and v.strip():
            return v.strip()
    die("No GitHub token found. Ensure org secret GH_STEGVERSE_AI_TOKEN is set and workflow passes env GH_TOKEN.")

def gh_api_json(args):
    token = get_token()
    env = os.environ.copy()
    env["GH_TOKEN"] = token
    out = subprocess.check_output(["gh"] + args, text=True, env=env).strip()
    return json.loads(out) if out else {}

def list_org_repos(org):
    data = gh_api_json(["repo", "list", org, "--limit", "200", "--json", "name,owner,isPrivate,defaultBranchRef"])
    return data or []

def ensure_git_identity():
    name = os.getenv("GIT_AUTHOR_NAME", "StegVerse-AI")
    email = os.getenv("GIT_AUTHOR_EMAIL", "stegverse-ai@users.noreply.github.com")
    sh(["git", "config", "--global", "user.name", name])
    sh(["git", "config", "--global", "user.email", email])

def clone_repo(full_name, workdir):
    token = get_token()
    url = f"https://x-access-token:{token}@github.com/{full_name}.git"
    if workdir.exists():
        shutil.rmtree(workdir)
    sh(["git", "clone", "--depth", "1", url, str(workdir)])

def current_default_branch(repo_dir):
    try:
        head = sh(["git", "symbolic-ref", "refs/remotes/origin/HEAD"], cwd=repo_dir, capture=True)
        return head.split("/")[-1]
    except Exception:
        return "main"

def make_branch_name(prefix="autopatch"):
    ts = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    return f"{prefix}/{ts}"

def add_standard_files(repo_dir):
    templates_dir = pathlib.Path(__file__).resolve().parent.parent / "templates"
    changed = False
    for rel in STANDARD_FILES:
        src = templates_dir / rel
        dst = repo_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            changed = True
    return changed

def push_with_pat(repo_dir, branch):
    token = get_token()
    origin = sh(["git", "config", "--get", "remote.origin.url"], cwd=repo_dir, capture=True)
    m = re.search(r"github\.com[:/](.+?)(?:\.git)?$", origin)
    if not m:
        die("Cannot parse origin URL to build PAT-auth push URL.")
    repo_full = m.group(1)
    authed_url = f"https://x-access-token:{token}@github.com/{repo_full}.git"
    sh(["git", "push", authed_url, branch], cwd=repo_dir)

def open_pr(full_name, head_branch, base_branch, title, body):
    token = get_token()
    env = os.environ.copy()
    env["GH_TOKEN"] = token
    try:
        url = subprocess.check_output(
            ["gh","pr","create","--repo",full_name,"--head",head_branch,"--base",base_branch,
             "--title",title,"--body",body],
            text=True, env=env
        ).strip()
        print(f"[SCW] PR created: {url}")
        return url
    except subprocess.CalledProcessError:
        die("PR creation failed. Token may lack Pull Requests write permission or a repo-level secret override is still present.")

def cmd_self_test(target_repo, org):
    print("[SCW] Command: self-test")
    print(f"[SCW] Target repo: {target_repo}")
    repos = list_org_repos(org)
    print(f"[SCW] Token can see {len(repos)} repos in {org}.")
    samples = ", ".join([f"{r['owner']['login']}/{r['name']}" for r in repos[:10]])
    print(f"[SCW] Sample repos: {samples}")
    gh_api_json(["repo","view",target_repo,"--json","name,defaultBranchRef"])
    print("[SCW] Self-test PASS.")

def cmd_autopatch(target_repo, org):
    print("[SCW] Command: autopatch")
    workdir = pathlib.Path("/tmp/scw_target")
    clone_repo(target_repo, workdir)
    base_branch = current_default_branch(workdir)
    print(f"[SCW] Target repo default branch: {base_branch}")

    ensure_git_identity()
    sh(["git","checkout","-b", make_branch_name()], cwd=workdir)
    changed = add_standard_files(workdir)
    if not changed:
        print("[SCW] No missing standard files. Nothing to patch.")
        return

    sh(["git","add","."])
    sh(["git","commit","-m","chore(autopatch): add missing StegVerse standard files"], cwd=workdir)
    branch = sh(["git","rev-parse","--abbrev-ref","HEAD"], cwd=workdir, capture=True)
    print("[SCW] Pushing branch with PAT-auth URL...")
    push_with_pat(workdir, branch)
    open_pr(target_repo, branch, base_branch,
            "chore(autopatch): add missing StegVerse standard files",
            "Automated by SCW autopatch. Please review and merge.")

def main():
    ap = argparse.ArgumentParser(prog="scw_core")
    ap.add_argument("command", choices=["self-test","autopatch"])
    ap.add_argument("--org", default=ORG_DEFAULT)
    ap.add_argument("--target-repo", required=True, help="e.g. StegVerse-Labs/TVC")
    args = ap.parse_args()

    if args.command == "self-test":
        cmd_self_test(args.target_repo, args.org)
    else:
        cmd_autopatch(args.target_repo, args.org)

if __name__ == "__main__":
    main()
