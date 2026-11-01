# Aegis Endgame Analysis — primary endgame source

Contents: source access; source hierarchy; worksheet semantics; calculation rules; refresh workflow. Full per-sheet audit: [aegis-audit.md](aegis-audit.md). Machine metadata: [aegis-source.json](../data/aegis-source.json).

## Access and provenance

Author: Aegis / @theaegisrelic. [Original workbook](https://docs.google.com/spreadsheets/d/1JM-0SlxVDAi-C6rGVlLxa-J1WGewEeL8Qvq4htWZHhY/edit?gid=1062099834#gid=1062099834). Audited permitted XLSX export retrieved 2026-11-01. Preserve author attribution and cite worksheet + exact row/cell alongside the original URL. Retrieval date, Status update date and effective sandbox are different fields. Do not label this a live synchronized database or a complete game encyclopedia.

Run from the skill directory (XLSX commands need openpyxl):

```sh
python scripts/aegis.py sheets
python scripts/aegis.py search "Cascade Point" --sheet Perks
python scripts/aegis.py row --sheet Perks 19
python scripts/aegis.py search "surrounded" --details
python scripts/aegis.py row --sheet "Exotic Armor (ignore)" 3 --include-history
python scripts/aegis.py math-check
python scripts/aegis.py import /absolute/path/to/downloaded.xlsx
```

The private local snapshot lives at `assets/private/aegis-endgame-analysis.xlsx`. Public packages intentionally omit that third-party workbook: download XLSX through the original's enabled Download menu, then import. Without a snapshot search returns only the dated bundled name/locator index, never fabricated effects. A different SHA means a new snapshot requiring review; the reader uses its actual Status metadata, but the bundled index/audit remains dated. Formula results are exported caches; this reader does not execute macros, external links, Apps Script or formulas. Missing caches are unknown.

## Source priority and conflicts

Start here for covered endgame PvE weapon choices, archetype profiles, perk/origin effects, gear sets, artifact mods, subclass building blocks and contextual encounter discussion. Use its own author dates and conditions. Then verify applicability to the requested patch. Bungie controls patch changes, disabling and game rules; the manifest and item instances establish identity and legal rolls; Court supplies dedicated stacking analysis; Data Compendium supplies detailed triggers and exceptions. Aegis itself attributes effect details to Data Compendium and reserve figures to Reserve/Mag sources. Trace those upstream when the exact coefficient matters.

Keep competing source claims separate, with their date and context. Do not silently replace the existing 9.7.0.3 numerical records with sheet prose or relabel them as today's values. No automated import into effects.json or the comparison engine is performed. An Attrition Orbs threshold summarized as a percent, rounded count and subsequent hit must be checked against archetype-specific rules before use. A question mark such as `1?%`, a blank, `N/A`, or a range is not a confirmed scalar. Distinguish INF (model unlimited), not-applicable and unknown.

## How to interpret the tabs

- Status declares per-tab freshness. `updated` means author-maintained, not independently validated against today's sandbox. `in progress` is partial. Transitions and Raid Mods are planned entries without exported worksheets.
- Shopping List groups roles and acquisition priorities. Numeric priority codes are not damage coefficients. Alternatives are conditional candidates, not equivalent simulations.
- Weapon tabs contain recommended perk lists, not exhaustive legal perk pools. Per Status!A38, two lists are independently ordered: never assume top + top is a valid or preferred combination. Verify every exact item/reissue hash, column, crafting/enhancement restrictions, catalyst and activity availability elsewhere. Preserve newline variants and reissues. Blank stun cells do not prove absence of champion interaction.
- S/A/etc ratings are editorial and relative to that specific tier list. S glaive does not equal S sniper. Do not convert tiers, tags, checkmarks, stars, row ranks or scoring formulas into measured DPS, DR or uptime.
- Most weapon schemas use B name, C season, D energy, E frame, F source, G stun, H Ammo, M/N perks, O origin, P notes, Q rank, R tier. H is a raw source field: it is not automatically shots in reserve. Heat weapon comments describe heat generation/cooling. Glaives add shield; swords have charge/impact; Traces omit frame and shift columns. Read actual row headers and comments rather than applying one positional schema to all tabs.
- Exotic Weapons separates usage dimensions (roam/DPS/challenge/speed); tags are not multipliers. Exotic Armor (ignore) and Builds (ignore) are author-excluded pre-TFS material. They cannot supply current armor mechanics or finished builds.
- Perks: B name, E trigger, F effect, G enhancement, H description, I usage. Origin Traits: E trigger, F effect, G notable weapons (examples, not full membership); effects are enhanced according to F2's comment. Set Bonuses: keep set name + 2/4-piece threshold distinct. Artifact Mods: preserve artifact identity; D tier is its artifact row and I tier is editorial. Do not equip mods from different eras as one artifact.
- Fragments: preserve subclass, trigger, effect and G stat tradeoffs. Aspects: preserve class/subclass and E fragment-slot count. Neither lists every ability scalar or all legal Prismatic combinations.
- Subclasses contains contextual loadout suggestions and editorial aggregates, not complete legal loadouts or numeric damage baselines. Some visual/icon cells do not survive XLSX; absent text must not be reconstructed as confirmed facts.
- Encounters grades strategy, gating, depth, fun and consistency. Its aggregate is not boss health, damage-window duration, resistance or enemy population. Use dedicated encounter evidence for those inputs.
- Changelog compares editorial rankings across named releases/eras; it is not the official numerical patch history. Historical sheets remain accessible only with explicit archival inclusion. Experimental is hypothetical future tuning dated 2024, not current sandbox data. Ideas is unfinished; hidden sheets are excluded by default.

## Mathematical use

Archetypes is a normalized archetype comparison, not a measured damage table for every named weapon/encounter. Inspect row formulas, notes, units and target before transporting any value to a rotation. No baseline sandbox or boss identity is inferred merely from a sheet update date.

Important columns: H base damage, I minor scalar, J elite scalar, K crit multiplier, L max ammo, M base interval, N optimized interval, O true RPM, P tested magazine, Q base reload, S base dump, T modded magazine, U modded reload, V modded dump, W max brick. R is unlabeled: do not give it an invented unit. X:AD are minor/elite DPS and editorial add score; AE:AI boss DPS variants/score; AJ:AM totals/brick; AN ADS range; AO notes; AP tier. Scores have row-specific formulas and must not be treated as physical units.

Header comments establish assumptions: Q includes one Loader and 100 Weapons; T assumes no magazine perk plus enhanced Backup Mag, with separate heat conditions; W uses 200 Weapons plus scavenger. Optimized interval can include charge/draw mods or back-to-back shots. Burst dump runs first shot to last shot. Sword rows encode specific heavy/light combos, extra damage and row-specific assumptions. Preserve these assumptions when comparing, rather than stacking a second Loader/Backup Mag benefit onto an already modded baseline.

For ordinary matching rows inspect formula relationships such as RPM = 60 / interval and typical boss DPS = damage * tested magazine / (reload + dump). A one-magazine shot sequence typically spans (n-1) intervals; a repeated full cycle adds the reload. Do not reuse the latter as the exact discrete damage in a short phase. The reader's math-check independently checks two standard relationships against cached values; exceptions are reported, not rewritten. It does not remeasure damage or certify arbitrary spreadsheet formulas.

Before comparing builds establish target, patch, power/scaling, crit access, range, phase length, movement, add density, ammo economy, setup/swap/reload, proc uptime and team effects. Obtain a compatible absolute damage baseline; do not mix these normalized values with unrelated boss HP. Use compare.py only with its documented explicit-event contract and compatible baseline metadata. Report survivability and utility separately. Include a scenario where the advantage reverses when supported by evidence.

## Refresh workflow

Open the original, inspect Status and relevant changelog sections, export through enabled controls, retain retrieval date and SHA, import, and audit changed schemas/values/comments before adopting them. Do not refresh the bundled index by assuming old row numbers. An author date can lag actual edits; state that uncertainty. Preserve historical snapshots separately when answering historical questions. This beta does not automatically download, synchronize, or validate every future patch.
