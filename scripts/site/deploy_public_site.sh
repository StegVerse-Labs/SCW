
#!/bin/bash
set -euo pipefail
bash scripts/site/validate_public_site.sh || true
bash scripts/site/sync_public_to_targets.sh
bash scripts/deploy/deploy_orchestrator.sh
bash scripts/status/publish_status.sh
