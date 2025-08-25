
Public Site
===========
Edit `site_public/` (index.html, roadmap.html, docs.html, community.html).

One-prompt publish to a separate website repo (e.g., StegVerse/site):
  scripts/site/one_prompt_public_site.sh

Cross-repo helpers:
  scripts/site/publish_to_external_repo.sh <owner/repo> [--domain stegverse.org]
  scripts/site/verify_external_pages.sh <owner/repo>
  scripts/site/pull_from_external_repo.sh <owner/repo>
  scripts/site/round_trip_sync.sh <owner/repo> [--republish] [--domain stegverse.org]
