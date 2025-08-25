
#!/bin/bash
set -euo pipefail
REPO="${1:?owner/repo}"; CUSTOM="${2:-}"; DOMAIN="${3:-}"
gh auth status >/dev/null 2>&1 || gh auth login -w
gh api -X POST repos/$REPO/pages -H "Accept: application/vnd.github+json" -f build_type="legacy" -F source='{"branch":"gh-pages","path":"/"}' >/dev/null 2>&1 || true
gh api -X PUT repos/$REPO/pages  -H "Accept: application/vnd.github+json" -f build_type="legacy" -F source='{"branch":"gh-pages","path":"/"}' >/dev/null
if [ "$CUSTOM" = "--custom-domain" ] && [ -n "$DOMAIN" ]; then
  git fetch origin gh-pages || true
  git checkout gh-pages || git checkout --orphan gh-pages
  echo "$DOMAIN" > CNAME; git add CNAME; git commit -m "chore(pages): set CNAME $DOMAIN" || true; git push origin gh-pages -f; git checkout -
fi
INFO=$(gh api repos/$REPO/pages -H "Accept: application/vnd.github+json" 2>/dev/null || true)
URL=$(echo "$INFO" | grep -oE '"html_url":"[^"]+"' | head -n1 | cut -d'"' -f4)
echo "[✓] Pages URL: ${URL:-https://<owner>.github.io/<repo>/}"
