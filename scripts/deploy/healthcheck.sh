
#!/bin/bash
set -euo pipefail
URL="${1:-}"; [ -z "$URL" ] && { echo "Usage: healthcheck.sh <url>"; exit 1; }
code=$(curl -s -o /dev/null -w "%{http_code}" "$URL" || true)
[ "$code" = "200" ] && echo "[✓] Healthcheck OK ($code)" || { echo "Healthcheck failed: HTTP $code"; exit 1; }
