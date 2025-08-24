
#!/bin/bash
# Pull public site content from an external repo into ./site_public (for safekeeping/editing).
# Priority order: gh-pages branch -> main branch.
# Usage: pull_from_external_repo.sh <owner/repo>
set -euo pipefail
TARGET="${1:?Usage: pull_from_external_repo.sh <owner/repo>}"
need(){ command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1"; exit 1; }; }
need gh
need git

gh auth status >/dev/null 2>&1 || gh auth login -w

TMP=$(mktemp -d)
git clone --depth=1 "https://github.com/$TARGET.git" "$TMP/repo"
cd "$TMP/repo"

# Prefer gh-pages content
if git show-ref --verify --quiet refs/heads/gh-pages; then
  git checkout gh-pages
else
  echo "[i] 'gh-pages' not found, using 'main'."
  git checkout main || git checkout -
fi

# Copy into SCW site_public
DEST="$OLDPWD/../../site_public"
mkdir -p "$DEST"
# Avoid overwriting .git etc in DEST; copy only site artifacts
shopt -s dotglob
rsync -a --exclude='.git' --exclude='.github' --exclude='node_modules' ./ "$DEST/"
echo "[✓] Copied site into $DEST"
