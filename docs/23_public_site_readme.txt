Public Site Docs
=================


Pull site content back into SCW
-------------------------------
If the public site repo was updated directly (e.g., contributors edited files there), you can pull changes back into SCW:
  scripts/site/pull_from_external_repo.sh <owner/repo>
This copies the gh-pages branch contents into SCW's site_public/ for safekeeping or rebuilds.


Bring site edits back into SCW
------------------------------
If collaborators edit the public site repo directly, you can sync those changes back here:
  scripts/site/pull_from_external_repo.sh <owner/repo>
This copies the repo's `gh-pages` (or `main` if `gh-pages` is missing) into `./site_public`.


Round-trip sync (pull → validate → deploy → (optional) republish)
-----------------------------------------------------------------
From SCW repo root:
  scripts/site/round_trip_sync.sh <owner/repo> [--republish] [--domain stegverse.org]

- Pulls site content from the external repo (gh-pages preferred) into `./site_public`.
- Validates links, deploys with fallbacks, republish back to the external repo if `--republish` is passed.


Roundtrip site edits (one-shot)
-------------------------------
Pull site from external → validate → republish back:
  scripts/site/roundtrip_external_site.sh <owner/repo> [--domain stegverse.org]


One-prompt public site setup (external repo)
--------------------------------------------
From SCW repo root:
  scripts/site/one_prompt_public_site.sh
- Defaults to `StegVerse/site` and `stegverse.org` but you can change both at the prompts.
- Publishes `site_public/` to the target repo's `gh-pages`, enables Pages, prints URL + DNS reminders.
