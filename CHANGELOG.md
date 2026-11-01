# Changelog

## 0.3-beta.1 — 2026-11-01 — experimental beta

- Aegis Endgame Analysis becomes the primary community source for covered endgame PvE topics, with Bungie, legal-roll and stacking checks retained.
- Audit of all 52 sheets, including 16 hidden sheets; per-tab author dates, source SHA, formula/comment counts, exclusions and documented schema differences.
- New read-only `aegis.py`: sheet inventory, name/detail search, exact rows with headers/formulas/comments, import and independent checks of standard archetype arithmetic against cached results.
- Dated name/row index works without the original. Local installation includes the downloaded XLSX; public release references the original and provides an import command because no full-workbook redistribution license was established.
- Guards for unrelated perk-column ordering, tier-list-local rankings, ignored pre-TFS armor/build tabs, hypothetical tuning, mixed artifact eras, uncertain values and normalized damage baselines.
- Preserves v0.2 mathematical tools and dated datasets without silently replacing their patch assumptions.

Still experimental: no complete sandbox simulator, exhaustive legal-roll solver, automatic source sync or independent validation of every source claim. Cached arithmetic checks do not validate in-game damage. v0.1 and v0.2 releases remain available.
