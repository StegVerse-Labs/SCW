
#!/bin/bash
set -euo pipefail
if ! command -v npx >/dev/null 2>&1; then echo "Install Node/npm to use linkinator/markdownlint"; exit 0; fi
npx --yes linkinator "site_public" --recurse --skip "mailto:,tel:"
if compgen -G "*.md" >/dev/null; then npx --yes markdownlint-cli "**/*.md" -i node_modules; fi
echo "[✓] Validation complete"
