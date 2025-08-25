
Repo Audit & Consistency
========================
Run:
  ./scripts/audit/repo_audit.sh
Checks:
- Branch protection on main (via gh)
- pre-commit hook presence
- Secret scanning configs
- .gitignore for secrets
- CI/Release/Status/Uptime/DCO workflows present
