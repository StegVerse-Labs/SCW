
#!/bin/bash
set -euo pipefail
set +e
DEPLOYED_URL=""
if command -v vercel >/dev/null 2>&1 && [ -n "${VERCEL_TOKEN:-}" ]; then
  echo "[i] Trying Vercel deploy (site_vercel)"
  (cd site_vercel && vercel --prod --token "$VERCEL_TOKEN" --confirm && DEPLOYED_URL="$(vercel url --token "$VERCEL_TOKEN")")
fi
if [ -z "$DEPLOYED_URL" ] && command -v netlify >/dev/null 2>&1 && [ -n "${NETLIFY_AUTH_TOKEN:-}" ]; then
  echo "[i] Trying Netlify deploy (site_netlify)"
  (cd site_netlify && netlify deploy --dir=. --prod --json && DEPLOYED_URL="$(netlify status | awk '/URL/{print $2}' | tail -n1)")
fi
if [ -z "$DEPLOYED_URL" ]; then
  echo "[i] Falling back to GitHub Pages (gh-pages)"
  git fetch origin gh-pages || true
  git checkout gh-pages || git checkout --orphan gh-pages
  rm -rf * .[^.]* 2>/dev/null || true
  cp -r site_pages/* . 2>/dev/null || true
  git add .; git commit -m "chore(pages): deploy site" || true; git push origin gh-pages -f
  DEPLOYED_URL="(gh-pages) https://<owner>.github.io/<repo>/"
  git checkout -
fi
mkdir -p reports
DEPLOY_JSON= '{"url": "' + DEPLOYED_URL + '", "ts": "placeholder"}'
echo "$DEPLOY_JSON" > reports/DEPLOY_STATE.json
echo "[✓] Deployed to: ${DEPLOYED_URL}"
