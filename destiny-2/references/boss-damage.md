# Aegis Boss Damage and ammo integration

Use alongside [Endgame Analysis](aegis.md). Boss Damage is the preferred community source for its measured baselines, rotation timings, team scaling and boss-specific considerations. Endgame Analysis remains the main contextual selection source. Detailed effect mechanics and stacking retain their dedicated sources.

Sources: [Aegis Boss Damage](https://docs.google.com/spreadsheets/d/1_5wtBjRYHHxuF4oJKDb_iOGZs-wTkzB6RYbnyNLbuz4/edit), [Mossy Magazine/Reserve Database](https://docs.google.com/spreadsheets/d/1l3xBHFa6ZMe86e13segg8f-RB8vLNerYEgNC_Aq3kLc/edit). Export snapshots retrieved 2026-11-01; local originals live under `assets/private`. Public packages contain an index, scoped factual observations and this integration, not full mirrors of source workbooks. Metadata and hashes: `data/workbooks.json`.

```sh
python scripts/workbooks.py boss sheets
python scripts/workbooks.py boss search "Hezen"
python scripts/workbooks.py boss row "Fireteam (S29)" 3
python scripts/workbooks.py boss row Weapons 229
python scripts/workbooks.py boss baseline Weapons 3 L --component weapon_impact
python scripts/workbooks.py reserves search "21% Delirium"
python scripts/workbooks.py reserves row "EoF Full Database" 10
python scripts/workbooks.py boss import /absolute/path/downloaded.xlsx
```

Commands need openpyxl for originals; a missing original permits only name/row index lookup. Export only through author-enabled controls. A new hash marks a new snapshot requiring audit; row numbers in the packaged index remain tied to its audited export. Historical, old, hidden, backup, copied and testing sheets are excluded by default. Explicit archival inclusion does not make them current recommendations.

For a new export, supply its actual acquisition date with import `--retrieved-at YYYY-MM-DD`. Import time is recorded separately. An unaudited file without a receipt retains an unknown retrieval date and a candidate baseline requires that date to be verified; it does not inherit the original snapshot's date.

## Interpret rows before calculating

- Boss Damage export has 24 worksheets. Changelog records completion of Fireteam (S29) and Graphing (S29) on 2026-10-31. This completion date does not update every underlying measurement patch.
- Weapons separates visible wipe-number observations (L normalized visual value) and healthbar-derived values (T), with source patch in U. These observations may differ. Preserve original modifiers, target normalization, number of hits and component interpretation.
- Abilties is the source's actual tab spelling. It distinguishes 100-stat and 200-stat observations and healthbar methods. Do not apply another stat multiplier on top of an already scaled value.
- Sustained and Swap contain configured comparisons, buffs, surge/debuff presets, cast/ready/stow timing and special assumptions. Some rows explicitly model pre-popped preparation, loadout-swap exploits or ideal interactions. The top row is not automatically a legal practical recommendation.
- Fireteam S29 / Graphing S29 address rotations/team scenarios. DPS columns at 10/20/etc seconds and cumulative event curves are different quantities. Inspect full row notes and team roles before using them.
- Bosses contains health, effective health, phase/range/setup/add considerations and enemy-specific exceptions. In-game HP and effective/normalized HP cannot be substituted across measurement units. Proxy bosses can have different applicability of crits, buffs and debuffs.
- Ammo Base Total Ammo includes the loaded magazine. Bigger magazines can change total reserves; don't add the magazine a second time. Keep specific roll, magazine/inventory stats, era and brick assumptions together.

The baseline export helper only supports numeric Weapons L/T values with a declared row patch, explicit caller-selected component label, and conditions that still require semantic review. It emits a candidate ledger record; it does not adopt it automatically or certify the supplied component label. An unknown patch/number is rejected.

The included archetype cross-check compared 47 unique compatible unmodified observations after explicit burst division; 46 agreed within rounding. This is same-author consistency, not independent game validation. Data: `data/archetype-crosscheck.csv`. Precision Scout remains an unresolved conflict in the ledger.
