
#!/bin/bash
set -euo pipefail
TARGET="${1:?Usage: pull_from_external_repo.sh <owner/repo>}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
DEST="$ROOT_DIR/site_public"
need(){ command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1"; exit 1; }; }
need gh; need git; need rsync
gh auth status >/dev/null 2>&1 || gh auth login -w
TMP=$(mktemp -d)
git clone --depth=1 "https://github.com/$TARGET.git" "$TMP/repo"
cd "$TMP/repo"
if git show-ref --verify --quiet refs/heads/gh-pages; then
  git checkout gh-pages
else
  echo "[i] gh-pages not found, using main"; git checkout main || git checkout -
fi
mkdir -p "$DEST"
rsync -a --exclude='.git' --exclude='.github' --exclude='node_modules' ./ "$DEST/"
echo "[✓] Copied site into $DEST"
