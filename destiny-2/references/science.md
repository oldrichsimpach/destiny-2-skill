# Destiny Science: access, operation and freshness

Read [coverage.json](../data/coverage.json) before choosing a source. It distinguishes access, calculation testing and data freshness. `verified_for_scope` never means the entire game, workbook or current patch has been verified. Numerical findings are in [effects.json](../data/effects.json), [facts.json](../data/facts.json) and [stat-samples.json](../data/stat-samples.json), with source IDs resolved through [sources.json](../data/sources.json). Search them with `scripts/knowledge.py search TEXT`.

## Obtain evidence

Follow the live [Destiny Science directory](https://www.destiny2.science/) link; record the actual workbook ID and tab gid. Read the author's instructions, warnings, effective sandbox and changelog. Different tabs can have different ages; an OLD tab or an abandoned planner is not a current dataset. A version display or recent Drive modified date does not certify coefficients.

Use source-authorized Download or Make a copy. If the owner disables these, use the permitted viewer. Do not circumvent limitations with export/gviz/forced-copy routes or hidden application state. A visible template's USE TEMPLATE button is an ordinary supported copy mechanism. Never edit the public original.

For an authorized private copy verify the title, distinct document ID and sharing setting. Do not activate copied Apps Script or an Allow access external-data prompt merely to test ordinary local formulas. Those features are separate from standard input cells. Two private copies in the v0.2 test were exercised without enabling their external imports or scripts.

Keep immutable permitted exports outside the installed skill, alongside source URL, exact acquisition time and SHA-256. The v0.2 local work folder is evidence, not a database to redistribute. Use `scripts/science_workbook.py` to inspect exports read-only: visible/hidden tabs, named ranges, validation, formula text, cached values, cached errors and compatibility wrappers. This helper needs openpyxl. It neither recalculates nor certifies the workbook. Null caches may be legitimately blank or missing.

Google functions such as REGEXMATCH or imported images can become `__xludf.DUMMYFUNCTION`; charts or Apps Script may not survive export. Formula text, a cached result and a successful download are three different observations.

## Operate and verify

Save baseline inputs and dependent results, change one variable, confirm it persists and affects a meaningful result, then restore all tested inputs. Do not mistake editing a field or a checkmark for completed recalculation. Inspect formula dependencies and export/cache values after the engine has processed the edit. If UI automation writes the wrong type, correct the input and repeat the affected test before claiming success.

In Google Sheets, select a visible tab and use its Name box for exact cells. Type into a selected cell only after exiting any active editor; `paste` can append to an active editor. Prefer the actual dropdown for labels beginning with `+` (e.g. `+10 Health`), since free text can be interpreted as a formula. Use checkbox controls for booleans where available. Re-read the selected coordinate and persisted value before further actions.

Observed landmarks (re-discover if a source changes):

| Source | Inputs | Results | v0.2 observation |
|---|---|---|---|
| Damage Generator, Database | B3 encounter; B5 custom seconds; C5 custom enabled; B8 apply buffs | B4 effective seconds; L15 modified adaptive-fusion damage; AV15 encounter damage | Default B4=20, B5=30, C5=false, B8=false. C5=true/B5=45 changed AV15; B8=true applied existing source selections. Restored all four inputs. |
| Damage Generator, Buffs/Debuffs | B4:B8 weaken options; B13:B17 empower; D19:D24 surges | Formula chain into Database!L15 | Source contains Radiant 25%, generic Tether 30%, Banner Shield 40%. These are stale compared with newer Court values. Do not silently rewrite the source and call it current. |
| Armor Planner, Build Planner | D14 helmet stat-mod dropdown | F2 Health, F4 Grenade, M3 orb healing, M10/M11 grenade factors | `+10 Grenade` -> `+10 Health` changed Health25->35, Grenade55->45; reset restored dependent values. |

These tests establish the specified input/output paths, not all weapons, perk interactions, plots or script features. Source absolute damage and stat modeling still require game-context validation.

## Freshness and historical records

Keep acquisition, author-updated, effective-patch and audited dates separate. Before current numerical use, check the latest official Bungie notes and later fixes relevant to the actual effects. A source can have correct mathematics and stale data. Record contradictions rather than overwriting history or applying a single relative percentage across multiple sandbox/power overhauls.

The initial v0.2 audit inspected official 9.7.0, .1, .2, .5 and .6 notes; .3/.4 notes were not retrieved. Court's own 9.7.0.3 certification does not close that gap. The stored Court subset therefore remains `partially_verified`, locked to that sandbox in the numerical helper. Updates .5 and .6 concern backend/cosmetics and do not themselves validate old damage numbers. Recheck newer information on each current-data request.

Ability-stat bonuses require their own baseline. Armor Planner cooldown factors are relative to its zero-stat base; they are not automatically a multiplier of an old pre-EoF cooldown. Energy bonus is not a reduction in seconds. Super stat energy gain is distinct from passive super cooldown. Keep ability-specific chunk scalars and damage components separate; v0.2 does not yet provide all such scalars.

## Clarity attribution

[Clarity](https://www.d2clarity.com/) is an external community research project. [Its usage requirements](https://www.d2clarity.com/partnerships) and [tooltip feedback Discord](https://d2clarity.com/discord) should accompany any future database integration. v0.2 routes to it without redistributing its database. Do not label Clarity tooltips as original measurements, strip credit, or mistake its update version for a Bungie patch.
