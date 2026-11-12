# History cleanup — 12 November 2026

## Scope

Repository: `deepdevjose/explainable-market`. Published branches: `main` and
`feat/multi-market-data-foundation`. The owner's explicit authorization allowed
replacement of their history; earlier commit identifiers changed. The separate
`ning-111/explainable_market` checkout belongs to another remote and was neither
modified nor published by this operation.

`git-filter-repo` was used with sensitive-data removal in a private copy:

- Historical removal of `env (1).txt`, `data/`, Python bytecode, the academic PDF
  containing old credentials and the legacy reference screenshot.
- Redaction of known historical secret values remaining in text and messages,
  including the configuration example. Their values are not included here.
- Preservation of functional changes and the current application; one public
  preparation commit groups the new documentation and checks.
- A private recovery copy outside the repository, in a mode-0700 directory with
  mode-0600 backup files. Do not share, publicly synchronize or upload it.

## Evidence

Before the final documentation update, 215 file versions from the two sanitized
branches were examined: no private paths, recognized credential patterns or
matches against known historical and service secrets were found. The current
tree matched the preparation commit before these reports were changed. Subsequent
changes only described the cleanup process.

All 79 tests, Ruff, mypy (23 selected files) and the index check passed in a
separate checkout of the sanitized version. Demo databases and private
configuration remained in their original locations. Cleanup does not constitute
credential rotation or a new deployment.

## Collaborators and limitations

Cloning the clean repository again is the simplest option for collaborators.
Do not merge old branches: they can reintroduce sensitive history. Preserve local
work first and apply only reviewed changes to the new version. Do not push the
recovery copy or another old clone.

Changing references cannot guarantee removal of caches, forks or external clones.
The earlier review found no remote pull-request references, but that does not
certify that GitHub purged every old object. A post-push check confirmed HTTP 200
and a known sensitive value at an old-history raw URL. Its contents are neither
saved nor reproduced here. Removal of that public copy remains pending: the owner
must request a purge from GitHub Support using [the official procedure](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).
Support may require that revocation alone cannot mitigate the risk. No support
request was sent and no third-party keys were revoked. A private support draft
was prepared outside the repository. Branch cleanup must not be presented as
complete elimination of the exposure.

Exposed credentials must be revoked even when absent from the branches. See
[SECURITY.md](../SECURITY.md). A targeted search is not a comprehensive security audit.
