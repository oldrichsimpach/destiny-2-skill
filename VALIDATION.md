# Validation — 0.4-beta.1 — 2026-11-01/02

64 functional tests passed with bundled Python and openpyxl. The suite includes the 18 v0.3 regression tests and 46 additional tests for the new evidence/state/constraint/update behavior.

Observable checks include:

- Patch, unit, mode, component and condition gates; unknown/stale claims; explicit conflict choice; assumption opt-in; invalidated claim blocking.
- Source-defined stacking groups cannot be renamed into independent groups; weapon factors cannot become ability or generic target factors.
- Ammo/reload conservation, no damage from zero ammo, charge/travel offsets, half-open windows, refill/overflow/pickup limits, movement/falloff, delayed/expired effects, hit-proc ordering and discrete ranking reversal.
- No completed reload after phase end or death; already airborne projectiles persist after death.
- Ability energy conservation, first-cast causality, distinct chunk/class scalars, recharge factor expiration and realized hit procs in seeded Monte Carlo.
- Typed DR groups, overshield-specific DR and overflow, timing and no resurrection from healing.
- Exact socket pools, currentlyCanRoll, class/slot/unique-label conflicts, owned plugs, crafting uncertainty, fragment/artifact constraints, mod budgets and audited slot/cost/copy rules.
- Cell and strikethrough changes flag dependents; unchanged snapshots do not. Array formula representations are stable/serializable. Official-patch mention review flags supplied result dependencies without changing coefficients.

Additional real-artifact checks:

- Manifest version `245114.26.10.13.2000-1-bnet.66137`, retrieved 2026-10-24: new Hezen `2265407516` supports the example Cluster Bomb / Elemental Honing socket memberships; old `4050645223` fails them. Positive output remains runtime-unverified, not complete legal certification.
- Boss Damage `Fireteam (S29)` row 3 reads successfully with 24 nonempty returned columns, including structured array formulas; export identity matches the audited source.
- Boss Damage fingerprint covers 24 sheets / 129,375 populated/formula/comment cells; Endgame fingerprint covers all 52 sheets. These are structural/value/cache observations, not recalculated game measurements.
- Synthetic encounter example: ideal final-window damage 600 vs 720; movement profile 600 vs 540; far profile 300 vs 720. Synthetic ability example casts at 0 and 6, with damage at 1 and 7; final energy 0.6, damage 340 by 12 seconds.
- Independent forward-testing executed 10/20-second hit-proc vs ability-refund fixtures under ideal and lower accuracy/movement profiles, the real manifest reissue checks, dependency invalidation, all bundled example CLIs, same-time proc/expiry cases and event-curve/window consistency. It confirmed the tools preserve synthetic and runtime-unverified labels.

During implementation real-source testing found array-formula JSON serialization needed a structured representation; fixed and regression-tested. Model review found a reload could appear completed outside the phase/death boundary; fixed and regression-tested.

Limits: no independent in-game retest, complete live stat/rule corpus or full-game simulation. Rule packs and literal coefficients need their own evidence. Probability outputs are finite estimates; sample traces are labeled trial 0. Historical v0.2 live spreadsheet-copy tests are not reclassified as newly rerun validation here. Public packages exclude originals, private monitor configuration, inventory data and generated caches.
