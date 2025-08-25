
StegVerse — Sovereign Control Workspace (SCW) — FULL Bundle
===========================================================
Includes: CI/CD, governance, fallback deploys, status/uptime, public site tools,
cross-repo publisher, one-prompt flows, and more.

Quick start (iPhone-friendly):
1) Upload zip to your repo (GitHub → Add file → Upload files → Commit).
2) Open Codespace → Terminal:
   unzip steg_scw_full.zip -d .
   rm steg_scw_full.zip
   git add .
   git commit -s -m "chore: import SCW full bundle"
   git push origin main
   scripts/util/doctor.sh
3) One-prompt setup (auth, branch protection, secrets, first deploy):
   ./scripts/one_prompt_setup.sh
4) Publish public site to external repo (e.g., StegVerse/site):
   scripts/site/one_prompt_public_site.sh
