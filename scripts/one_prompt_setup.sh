
#!/bin/bash
set -euo pipefail
need(){ command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1"; exit 1; }; }
need git; need gh
gh auth status >/dev/null 2>&1 || gh auth login -w
if ! git remote get-url origin >/dev/null 2>&1; then
  read -r -p "Create new GitHub repo now? (Y/n): " CR
  if [[ -z "$CR" || "$CR" =~ ^[Yy]$ ]]; then
    read -r -p "Enter <owner/repo>: " FULL
    read -r -p "Make private? (y/N): " PRV; [ "$PRV" = "y" -o "$PRV" = "Y" ] && PRIV="--private" || PRIV=""
    scripts/github/create_repo_and_push.sh "$FULL" $PRIV
  else
    echo "Set origin and re-run."; exit 1
  fi
fi
ORIGIN="$(git remote get-url origin)"
if [[ "$ORIGIN" =~ github.com[:/]+([^/]+)/([^/.]+) ]]; then FULL="${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"; else read -r -p "Enter <owner/repo>: " FULL; fi
read -r -p "Require signed commits? (Y/n): " RS; [ -z "$RS" -o "$RS" = "Y" -o "$RS" = "y" ] && SIGN="--require-signed" || SIGN=""
scripts/github/ensure_branch_protection.sh "$FULL" $SIGN
scripts/github/set_common_secrets.sh "$FULL" || true
read -r -p "Install auto Signed-off-by hook? (Y/n): " HOOK; [ -z "$HOOK" -o "$HOOK" = "Y" -o "$HOOK" = "y" ] && scripts/git/install_signedoff_hook.sh || true
./scripts/first_run.sh || true
echo "[✓] One-prompt setup complete."
