import os, json, subprocess, tempfile, pathlib, datetime

ORG = os.getenv("ORG_GITHUB", "StegVerse-Labs")

def log(msg):
    print(f"[SCW] {msg}", flush=True)

def gh(*args):
    cmd = ["gh"] + list(args)
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip() or res.stdout.strip())
    return res.stdout.strip()

def list_org_repos():
    out = gh("api", f"orgs/{ORG}/repos", "--paginate", "--jq", ".[].full_name")
    return [line for line in out.splitlines() if line.strip()]

def get_default_branch(repo_full):
    return gh("api", f"repos/{repo_full}", "--jq", ".default_branch")

TEMPLATES_DIR = pathlib.Path("scw/templates")

def ensure_file(repo_dir: pathlib.Path, rel_path: str, template_name: str, replacements=None):
    replacements = replacements or {}
    target = repo_dir / rel_path
    if target.exists():
        log(f"Exists: {rel_path} (skip)")
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    template = (TEMPLATES_DIR / template_name).read_text()
    for k, v in replacements.items():
        template = template.replace(k, v)
    target.write_text(template)
    log(f"Added: {rel_path}")
    return True

def cmd_self_test(target_repo=None):
    log("Running self-test...")
    repos = list_org_repos()
    log(f"Token can see {len(repos)} repos in {ORG}.")
    if target_repo:
        branch = get_default_branch(target_repo)
        log(f"Target repo default branch: {branch}")
    log("Self-test PASS.")

def cmd_autopatch(target_repo):
    log(f"Autopatch starting for {target_repo}...")

    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise SystemExit("No GH_TOKEN/GITHUB_TOKEN available to autopatch.")

    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        repo_dir = td / "repo"

        log("Cloning repo...")
        gh("repo", "clone", target_repo, str(repo_dir))

        default_branch = get_default_branch(target_repo)
        date_tag = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        branch_name = f"autopatch/{date_tag}"

        subprocess.check_call(["git", "checkout", "-b", branch_name], cwd=repo_dir)

        # Ensure pushes authenticate with the PAT
        authed_origin = f"https://x-access-token:{token}@github.com/{target_repo}.git"
        subprocess.check_call(["git", "remote", "set-url", "origin", authed_origin], cwd=repo_dir)

        changed = False
        module_name = target_repo.split("/")[-1]

        changed |= ensure_file(repo_dir, ".github/workflows/scw_bridge_repo.yml", "SCW_BRIDGE_REPO.yml")
        changed |= ensure_file(repo_dir, "SECURITY.md", "SECURITY.md")
        changed |= ensure_file(repo_dir, "stegverse-module.json", "stegverse-module.json",
                               replacements={"{{MODULE_NAME}}": module_name})
        changed |= ensure_file(repo_dir, "README.md", "README_MODULE.md",
                               replacements={"{{MODULE_NAME}}": module_name})

        if not changed:
            log("No changes needed. Autopatch PASS (no-op).")
            return

        log("Committing changes...")
        subprocess.check_call(["git", "add", "."], cwd=repo_dir)
        subprocess.check_call(["git", "commit", "-m",
                               "chore(autopatch): add missing StegVerse standard files"], cwd=repo_dir)

        log("Pushing branch...")
        subprocess.check_call(["git", "push", "origin", branch_name], cwd=repo_dir)

        log("Opening PR...")
        pr_url = gh("pr", "create", "--repo", target_repo, "--base", default_branch, "--head", branch_name,
                    "--title", "Autopatch: add missing StegVerse standard files",
                    "--body", "SCW Autopatch Guardian added missing standard files (bridge workflow, SECURITY.md, module manifest, README skeleton).")

        log(f"PR created: {pr_url}")
        log("Autopatch PASS.")

def cmd_sync_templates(target_repo=None):
    log("sync-templates not implemented yet (stub PASS).")

def cmd_standardize_readme(target_repo):
    log("standardize-readme not implemented yet (stub PASS).")

def main():
    event = os.getenv("SCW_EVENT_NAME", "")
    input_cmd = os.getenv("SCW_INPUT_COMMAND", "") or "self-test"
    input_target_repo = os.getenv("SCW_INPUT_TARGET_REPO", "") or None
    input_args_json = os.getenv("SCW_INPUT_ARGS_JSON", "") or None
    dispatch_payload = os.getenv("SCW_DISPATCH_PAYLOAD", "")

    cmd = input_cmd
    target_repo = input_target_repo
    args = {}

    if event == "repository_dispatch" and dispatch_payload:
        try:
            payload = json.loads(dispatch_payload)
            cmd = payload.get("command", cmd)
            target_repo = payload.get("target_repo") or payload.get("target") or target_repo
            args_text = payload.get("args_text")
            if args_text and args_text.strip().startswith("{"):
                args.update(json.loads(args_text))
        except Exception as e:
            log(f"Failed to parse dispatch payload: {e}")

    if input_args_json:
        try:
            args.update(json.loads(input_args_json))
        except Exception as e:
            log(f"Failed to parse args_json: {e}")

    log(f"Command: {cmd}")
    log(f"Target repo: {target_repo or '(none)'}")
    log(f"Args: {args or '{}'}")

    if cmd in ("self-test", "selftest"):
        cmd_self_test(target_repo)
    elif cmd == "autopatch":
        if not target_repo:
            raise SystemExit("autopatch requires target_repo")
        cmd_autopatch(target_repo)
    elif cmd in ("sync-templates", "sync_templates"):
        cmd_sync_templates(target_repo)
    elif cmd in ("standardize-readme", "standardize_readme"):
        if not target_repo:
            raise SystemExit("standardize-readme requires target_repo")
        cmd_standardize_readme(target_repo)
    else:
        raise SystemExit(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
