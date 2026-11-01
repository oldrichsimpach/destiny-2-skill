# Validation — 0.3-beta.1

Run 2026-11-01 with bundled Python and openpyxl.

- Skill frontmatter/scaffold validator: passed.
- 18 functional tests passed: eight reader tests plus ten preserved numerical/provenance tests from v0.2. Reader tests cover excluded sheets, explicit historical access, uncertainty/comments/read-only behavior, detail search, index-only fallback, arithmetic mismatch detection, wrong-source rejection and Unicode output under a Windows legacy code page. Tests create synthetic fixtures and do not require redistributing original workbooks.
- Original export: 52 worksheets (36 visible / 16 hidden), 3,867 formulas, 107 comments, zero cached error cells. All worksheet structures and Status metadata scanned; source comments and semantic interpretation reviewed. This does not verify every source claim in-game.
- Independent arithmetic cross-check on original Archetypes caches: 174 standard RPM / typical cycle DPS relationships matched; 14 unsupported/special cases skipped; zero mismatches. No full spreadsheet recalculation.
- Independent behavior evaluation: correctly distinguished tier rankings from boss DPS, independently ordered perk lists from legal pairs, and ignored pre-TFS armor from current recommendations. It found a Windows Unicode output defect; fixed and regression-tested.
- The original source workbook was not edited. Local snapshot hash: `c71a2dc392225e8e88695d9ce892e82ca8ddc087d45250039e806769794a874d`.

Bounds: no automatic adoption of Aegis prose into effects.json, no full sandbox validation, no precise 12-second boss rotation without compatible measurements. v0.2 live-copy recalculation checks are historical validation, not rerun or claimed as new here. The public ZIP excludes original/private source exports and generated caches.
