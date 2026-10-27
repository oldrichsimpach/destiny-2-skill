# Curated lookup and bounded calculations

Python 3 standard library suffices for `knowledge.py` and `compare.py`; only XLSX inspection needs openpyxl. Paths below are relative to this skill directory.

```text
python scripts/knowledge.py search Radiant
python scripts/knowledge.py stat --value 100
python scripts/knowledge.py stack --ids radiant well surge-3 tractor --mode PvE --sandbox 9.7.0.3 --allow-partial
python scripts/compare.py examples/conditional-comparison.json
```

The stack example returns `1.25 * 1.22 * 1.30 = 1.9825`: Well suppresses the weaker Radiant empowerment. It is an explicit partially verified historical-sandbox scenario, not a current loadout recommendation. Radiant's effects on certain Supers are outside this weapon-only calculation. Armour/exotic surge tiers use the highest same-element tier, not a sum of tier counts.

## Data contract

- `sources.json`: source IDs, authors, direct URLs, inspected scope.
- `effects.json`: supported standard weapon buff/debuff/surge factors, PvE/PvP splits, duration when known, activation conditions, same-category precedence and sandbox. This is a selected subset, not every effect.
- `facts.json`: actual perk timings, historical mismatches, conditional rules and official patch deltas. Relative patch changes are not absolute base damage. Not every fact is executable as a multiplier.
- `stat-samples.json`: selected community formula/cache samples at 0,50,70,100,150,200. No interpolation or blanket PvP validity is implied. Null remains unknown/not applicable, never silently zero. Source name, metric, units and baseline accompany each record.
- `coverage.json`: the required coverage/status report. Use each record's scope and limitations, not merely its label.

`knowledge.py stack` rejects unknown effects, duplicate IDs, unsupported modes, mismatched sandboxes and partially verified records without explicit opt-in. This blocks accidental mixing; it does not prove ownership, legal perk pairing, elemental match, proc activation or team composition. The caller must verify those conditions first. Buff durations are not automatically simulated.

## Event comparison

`compare.py` evaluates explicit events in `[0,T)` with event time defined as hit time. Each scenario requires sandbox, mode, target, damage baseline, baseline_sandbox, baseline_kind (synthetic/measured/assumed), provenance, windows and named builds. Baseline and optional event-level baseline sandboxes must match the scenario. These fields are caller declarations; the program cannot independently determine the age or truth of a supplied damage number. Each event has `time`, `body`, optional `crit`, `hit_probability`, `crit_given_hit`. Its expected damage is `p_hit*(p_crit*crit+(1-p_crit)*body)`.

Optional `effect_ids` require `component: "weapon"` and `conditions_satisfied: true`. List only effects actually active at that event. Explicit event lists represent setup, swapping, misses, movement and temporary buff windows; the engine does not infer them. It does not solve RNG-dependent activation, ability energy loops, loadout legality, power scaling, rounding-specific PvP TTK or enemy behavior.

The `shots(ammo, magazine, interval, reload_gap, first_hit)` helper generates bounded shot times with a clearly defined reload gap: elapsed seconds from the last shot in a magazine to the first shot in the next. It does not add another firing interval on top of that gap. Initial charge/setup/projectile flight belongs in `first_hit`; changing cadence, bursts and DoT need explicit schedules.

Optional survival uses HP divided by the product of remaining-damage factors. Supply only independently stacking, verified DR for the same damage type and state. Invulnerability, healing, shield gates and overshield-specific interactions require a separate model.

The bundled example deliberately uses synthetic damage units to demonstrate a ranking reversal after setup time. It is not a measured Destiny loadout. For a real comparison replace the event data and provenance with matched, patch-specific measurements and state remaining uncertainty. Keep damage, survival and utility separate.
