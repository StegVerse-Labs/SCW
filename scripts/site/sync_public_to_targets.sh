
#!/bin/bash
set -euo pipefail
SRC="site_public"; for d in site_vercel site_netlify site_pages; do mkdir -p "$d"; rsync -a --delete "$SRC"/ "$d"/; done
echo "[✓] Synced public site to targets."
