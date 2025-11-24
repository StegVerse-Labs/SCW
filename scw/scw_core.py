import os, json, sys, textwrap, datetime, subprocess

ORG = os.getenv("ORG_GITHUB", "StegVerse-Labs")
SCW_REPO = os.getenv("SCW_REPO", "")

def log(msg):
    print(f"[SCW] {msg}", flush=True)

def gh(*args):
    cmd = ["gh"] + list(args)
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip() or res.stdout.strip())
    return res.stdout.strip()

def get_default_branch(repo_full):
    return gh("api", f"repos/{repo_full}", "--jq", ".default_branch")

def list_org_repos():
    out = gh("api", f"orgs/{ORG}/repos", "--paginate", "--jq", ".[].full_name")
    return [line for line in out.splitlines() if line.strip()]

def cmd_self_test(target_repo=None):
    log("Running self-test...")
    repos = list_org_repos()
    log(f"Token can see {len(repos)} repos in {ORG}.")
    sample = repos[:10]
    log("Sample repos: " + ", ".join(sample))
    if target_repo:
        branch = get_default_branch(target_repo)
        log(f"Target repo default branch: {branch}")
    log("Self-test PASS.")

def cmd_autopatch(target_repo):
    # placeholder - real autopatch comes next phase
    log(f"Autopatch requested for {target_repo}. (stub)")
    log("Autopatch stub PASS.")

def cmd_sync_templates(target_repo=None):
    log("Sync-templates (stub). We'll wire templates next.")
    log("Sync-templates stub PASS.")

def cmd_standardize_readme(target_repo):
    log(f"Standardize README for {target_repo} (stub).")
    log("Standardize README stub PASS.")

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
    elif cmd in ("autopatch",):
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
