
#!/bin/bash
set -euo pipefail
REPO="${1:?owner/repo}"; NAME="${2:?SECRET_NAME}"; VAL="${3:-}"
if [ -z "$VAL" ]; then read -r -p "Enter secret value for $NAME: " VAL; fi
printf "%s" "$VAL" | gh secret set "$NAME" -R "$REPO" -b-
echo "[✓] Set secret $NAME in $REPO"
