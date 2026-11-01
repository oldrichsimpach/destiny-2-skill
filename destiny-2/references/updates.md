# Source changes and dependent results

The monitor is a review/invalidation pipeline. It never adopts coefficients, extends patch validity, edits public originals or publishes a release on its own.

1. Retrieve a permitted new snapshot through the source's enabled controls. For restricted workbooks, inspect the allowed viewer and record relevant changed evidence manually; do not force-export.
2. Preserve the old immutable snapshot, the retrieval date, source URL and hash. Use a separate file for the new one.
3. Fingerprint and compare. Read the resulting changed rows/comments/formulas/formatting and official patch notes.
4. Mark dependent claims/results for review. Update factual records only after interpreting their units, conditions and effective sandbox. Preserve historical variants.

```sh
python scripts/audit_sources.py snapshot old.xlsx --source-id boss --out old-audit.json
python scripts/audit_sources.py snapshot new.xlsx --source-id boss --out new-audit.json
python scripts/audit_sources.py diff old-audit.json new-audit.json --result comparison.json --out review.json --state assets/private/review-state.json
python scripts/audit_sources.py patch official-patch.json --result comparison.json --out patch-review.json --state assets/private/review-state.json
```

Use writable absolute paths for user work. Writing the optional review state is explicit. Simulations automatically consult the installed skill's private state when present; a scenario can select an external `review_state` path. Invalidated claim IDs are refused until their evidence is reviewed and their state is deliberately cleared. Do not clear review flags just to obtain a number.

A local-only `assets/private/monitor-config.json` may point `review_state` to a writable external file. This lets the user's scheduled monitor persist flags without changing the installed code or public data. That machine-specific configuration is excluded from public packages.

XLSX fingerprints include formula text, cached values, comments, links, visibility, merges and formatting including strikethrough. This matters when text formatting distinguishes PvE/PvP or obsolete instructions. Fingerprints do not recalculate sheets. Full-file SHA changes may be export metadata only; semantic differences are reported separately. Claim watches are conservative row/header ranges, not a complete spreadsheet dependency parser.

SQLite fingerprints cover InventoryItem and PlugSet definitions plus manifest metadata. Any changed manifest can invalidate a prior structural legality result, independently of damage claims. Synchronizing the manifest is a separate existing `manifest.py sync` operation and does not prove current damage mechanics.

Patch review accepts an explicit document with `patch`, `published_at`, official HTTPS Bungie `url`, and `text`. Entity/alias mention matches mark related claims and supplied result files for review. They do not prove that a coefficient changed. Generic mechanics changes, renames and indirect dependencies can be missed, so read the complete applicable notes. Lack of a match is not evidence of unchanged mechanics.

For recurring checks, retain a persistent per-source baseline and compare each successful observation with the previous one. Keep the original baseline for traceability. Quiet unchanged runs; notify only about a meaningful new change, failed check or required user action. A repeated already-reported change should not produce another alert without new information. An inaccessible source is a failed check, not a successful unchanged result. Recurring scheduling is configured separately according to the user's chosen frequency; the scripts themselves create no background service.
