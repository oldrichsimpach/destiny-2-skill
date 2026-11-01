# Event/state simulation

Use `scripts/simulate.py` for finite rotations, triggered effects, abilities, incoming damage, accuracy sensitivity and range/movement profiles. Use `compare.py` for the older explicit-hit-only contract. Their reload inputs have different definitions; do not copy a reload number between them without translating the timing.

## Run and inspect

```sh
python scripts/simulate.py examples/encounter-demo.json --out comparison.json
python scripts/simulate.py examples/ability-loop-demo.json --summary
python scripts/optimize.py examples/encounter-demo.json --out frontier.json
python scripts/optimize.py candidates.json --inventory inventory.json --db /absolute/path/manifest.sqlite
python scripts/survivability.py survival-scenario.json
```

The bundled examples use synthetic numbers and synthetic item identities. They demonstrate engine behavior, not Destiny recommendations or measured builds. Read `result_kind`, assumptions, qualifications and skipped procs alongside the numbers.

Required scenario fields: `sandbox`, `mode` (PvE/PvP), `target` object, `damage_unit`, `baseline_kind` (synthetic/measured/assumed), `provenance`, `duration` (0<T<=3600), `builds`. Optional `windows_seconds`, `profiles`, `stochastic_trials`, `seed`, `allow_partial`, `allow_assumptions`, `satisfied_conditions`, `conflict_choices`, `review_state`. Every damage/HP input for the outgoing target must use the same damage unit. Baseline metadata and bare caller inputs do not establish measured truth.

Numerical game parameters can be `{"claim":"claim-id"}` references; see [evidence-and-legality.md](evidence-and-legality.md). Explicit literals can be `{"value":3.5,"unit":"seconds","provenance":"measured clip or declared assumption"}`. Non-synthetic literals require `allow_assumptions:true` and remain assumptions even when their provenance sounds authoritative. Unknown coefficients cannot be filled with zero. Arrays/counts/resource budgets are caller declarations and need separate verification for real builds.

## Timing and weapon resources

Actions run in listed order. `at` may advance time but cannot move before the previous action's animation/cadence lock. All events use `[0,T)`: an impact exactly at the window end is excluded.

A weapon has `id`, `ammo` (total including loaded), `magazine`, `components`, and timing fields in seconds:

- `charge_seconds`: before each discharge.
- `recovery_seconds`: action lock after each discharge. Next charge, reload or swap begins after it.
- `reload_seconds`: from the end of that lock to a newly loaded magazine. The last-discharge-to-next-discharge gap therefore includes recovery + reload + next charge. If a measured source gives the complete gap, split it explicitly; do not add recovery twice. Reload cancelling is not inferred.
- `ready_seconds` and `stow_seconds`: additive equip animation costs.
- `ammo_cost`: rounds per discharge (default 1); a burst may consume multiple rounds. A component's ticks do not independently consume ammo.

`initial_weapon` is already equipped at phase start. Otherwise the first equip pays its ready cost. `setup_seconds` is inside the modeled window; missing outside-window preparation must be stated as a separate condition.

Actions:

```json
{"type":"fire","weapon":"rocket","count":3,"auto_reload":true}
{"type":"reload","weapon":"rocket"}
{"type":"equip","weapon":"special"}
{"type":"wait","seconds":2}
{"type":"ammo_pickup","weapon":"rocket","rounds":2}
```

Empty magazines require an explicit reload action or `auto_reload:true`. Ammo pickups respect `ammo_capacity` (defaults to initial total), do not automatically refill the loaded magazine, and report waste. Ammo arithmetic preserves initial + gained - spent = remaining.

Optional passive `refill` rules have `scope` (`stowed` or `not_firing`), `delay_seconds`, optional `repeat_seconds`, explicit `rounds_per_tick` and `capacity_rounds`. Stowed timers cancel on ready; idle timers reset on discharge. Refills move existing ammo into the magazine, including declared overflow; they never create ammo. For Reconstruction/ALH, verify the actual per-weapon rounding, timer semantics and era before configuring this generic rule. A source's 25% summary is not automatically a known integer refill count.

## Components, range and probabilities

Components have unique `id`, `kind` (`weapon_impact`, `weapon_explosion`, `weapon_combined`, `dot`, `ability`, `super`), `body`, optional `crit`, `element`, `hit_probability`, `crit_given_hit`, and `offsets` (relative to discharge; use for travel and ticks).

`weapon_combined` preserves an observation whose impact/explosion split is unknown. It does not authorize applying a component-specific perk to the whole number. Body fallback for omitted crit means the same damage, not an invented crit multiplier.

`snapshot:"fire"` captures active damage factors at discharge; `snapshot:"hit"` evaluates them on impact. Choose from evidence for the specific component. Delayed ability components are emitted after its cast time. In-flight attacks can land after actor death; no later player actions occur after death. Cancellation of an already cast ability on death is not inferred.

`counts_for_triggers:true` explicitly permits a component's impacts to count towards hit/crit procs. Without it, merely having damage does not establish hit-count semantics. Verify pellet, burst, explosion and DoT counting rules. `accuracy_group` groups components/ticks that share a stochastic hit/crit draw for the same owner and discharge; use different groups for independent outcomes. It does not simulate arbitrary enemy geometry or correlated failures across different attacks.

Range is optional and never guessed. `falloff_points:[[distance_m,factor],...]` needs measured ordered points with nonincreasing factors. Target/profile `distance_m` must lie within the sampled range. Between points, linear interpolation requires `falloff_interpolation:"linear"`; otherwise only exact samples are accepted.

Profiles can declare `id`, `hit_scale`, `crit_scale`, `extra_setup_seconds`, `movement_windows`, `distance_m`, and boolean `effect_availability` keyed by effect ID. Movement windows delay actions, while projectiles already in flight continue. `target.vulnerability_windows` determines whether impacts deal damage and count as hits. Scenarios do not infer these windows from a boss name.

## Effects and nonlinear triggers

Effects have `id`, `kind` (damage/recharge/instant), `duration_seconds`, optional `icd_seconds`, `activation_delay`, `refreshable`, `requires_conditions`. Damage/recharge effects require an explicit `category`, `stacking` rule (`max`, `product`, `sum_bonus`) and `factor`. All effects in a category must use the same rule. Only apply a category policy after verifying it for the requested patch; arbitrary category names are caller assumptions, not proof of independence. Repeated activation of the same timed ID refreshes its duration when permitted, rather than stacking copies.

Damage effects require explicit `components`; optional `weapon_ids` and `element` restrict scope. Recharge effects require `ability_ids`. Activate manually with `{"type":"activate","effect":"id"}` or configure a trigger:

Source-referenced factors must retain their recorded component/role scope. Known source stacking groups cannot be renamed into independent categories to multiply otherwise exclusive buffs. A weapon factor cannot be repurposed as ability recharge, energy gain or generic target scaling.

```json
{"on":"hit","source_ids":["a","b","c"],"distinct_sources":["a","b","c"],"within_seconds":7}
```

Triggers support fire, hit, crit, cast, kill and pickup; `count` sets a threshold. Hit procs activate after simultaneous impact damage, so the triggering hit does not gain the new buff. Source-specific first-shot behavior still needs evidence. The `distinct_sources` list is a declared requirement, not automatic Bait and Switch implementation.

Kills and pickups can be external `signal` actions with explicit `provenance`. Enemy kills are never inferred from fractional expected damage. Treat such signals as assumptions unless independently established; ensure the target/weapon identity and feedback-loop causal order match the gameplay.

Default probability mode computes expected damage for each supplied component. Probabilistic hit/crit counts cannot establish deterministic threshold procs: these procs are skipped, logged and qualified. Do not call that a complete expected rotation. Use `stochastic_trials` (1..2000) and a `seed` for nonlinear proc experiments. Each trial draws actual hits/crits, executes resource/proc state, and yields window means and p10/p50/p90 sample quantiles. These are finite Monte Carlo estimates, not exact probabilities. Mean curves are aggregated; resource/effect/survival traces and HP-crossing times are explicitly trial 0. A reported expected-damage crossing is not stochastic expected TTK.

## Ability loops and survival

Ability entries have `id`, `cooldown_seconds`, `cast_seconds`, `max_charges`, `initial_energy` in charges, and components. Recharge is sequential at 1/cooldown charges per second before timed recharge factors. Cast consumes one charge before its trigger/refund. `{"type":"cast","ability":"id","auto_wait":true}` waits for valid energy; without auto_wait insufficient energy is an error. No cast can fund its own first activation without an initial/external resource.

Effects can contain `energy_grants:[{"ability":"id","amount":0.2,"chunk_scalar":0.5,"class_mod_scalar":1}]`. Amount is in normalized charges; factors apply once. Grants and passive recharge are capped, with actual/wasted gains logged. Refunding a full charge, speed regeneration and a flat partial grant require different configurations. This does not supply unmeasured CES/CMS or current stat curves.

Build `survival` uses the contract below and joins the event queue. Effects can emit `heals:[{"amount":20}]` only when a survival model exists. Incoming events occur before damage/procs at equal timestamps; proc healing follows damage. Healing does not revive. This explicit ordering is a model convention that needs adjustment if a real mechanic depends on a different order.

Survival fields: `max_hp`, optional `initial_hp`, `health_unit` (default hp), `events`, `overshields`, `resistances`. Overshields are ordered pools with `id`, `capacity`, optional `initial`, `start`, `end`, `dr` and optional damage types. Resistance entries require `id`, `fraction`, `independence_group`, explicit `damage_types`, start/end and optional `requires_tags`. Same-group DR uses max; independent groups multiply remaining damage. Invulnerability is a timed zero-damage state, not finite EHP. Pool-specific DR applies only while damage is absorbed by that pool; overflow is converted correctly before reaching health.

Events are `incoming` with amount/type/tags, `heal` with amount, or `shield_grant` with amount/shield_id. Standalone survival preserves same-time input order; the combined simulator uses the queue priorities above. Enemy attack schedules, recovery and damage gates must be supplied; none is inferred.

## Comparing candidates

`lead_changes` reports the hit times at which cumulative leadership changes. A hit at t counts for windows ending after t; no linear interpolation is invented between discrete hits. Monte Carlo lead changes describe the estimated mean curve, not a guarantee for every trial.

`optimize.py` filters a supplied candidate list against exact declared owned instance/hash pairs and optional manifest/rule checks, then returns Pareto fronts for damage at all requested windows and compatible survival objectives. It never generates every possible Destiny loadout or proves global optimality. Unknown legality stays visible. Ammo quantities of different weapon types and qualitative utility are reported separately, not converted into an arbitrary universal score. For risk-sensitive choices inspect quantiles, source uncertainty and conditions alongside the mean ranking.
