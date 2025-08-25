
#!/bin/bash
set -euo pipefail
HOOK=".git/hooks/prepare-commit-msg"; mkdir -p "$(dirname "$HOOK")"
cat > "$HOOK" <<'H'
#!/bin/sh
SOB="$(git var GIT_AUTHOR_IDENT | sed -E 's/^([^<]+) <([^>]+)>.*/Signed-off-by: \1 <\2>/')"
grep -qi "^Signed-off-by:" "$1" || printf "\n%s\n" "$SOB" >> "$1"
H
chmod +x "$HOOK"; echo "[✓] Signed-off-by hook installed."
