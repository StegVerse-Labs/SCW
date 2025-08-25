
#!/bin/bash
set -euo pipefail
./bootstrap.sh
bash scripts/site/sync_public_to_targets.sh
./scripts/deploy/deploy_orchestrator.sh
./scripts/status/publish_status.sh
echo "[✓] First run complete."
