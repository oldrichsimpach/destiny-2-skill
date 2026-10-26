# Quantitative builds and comparisons

## Pin the scenario

Specify patch, PvE/PvP, class and allowed equipment, solo/team roles, activity/difficulty and modifiers, effective power delta, target classification, crit behavior, range, damage window, ammo/refill budget, enemy density, movement, player accuracy and activation reliability. Use explicit reasonable assumptions if unspecified. Never compare raw numbers measured on different targets without a validated normalization.

## Model damage as events

For each shot, projectile, explosion, tick, ability, summon or super: record timestamp, source, target, base damage and baseline, hit/crit probability, damage component, applicable multipliers, ammo/energy change, activation state and provenance. Handle precision and nonprecision components separately. Include reload, charge/draw, burst cadence, swap, travel, animation locks, warm-up, setup and expiration. Continuous beams, damage-over-time, overflow and auto-reload need their actual schedules.

Compute cumulative expected damage D(T) from events within the chosen window, DPS(T)=D(T)/T, total reserve damage and time to ammo exhaustion. Define boundary convention for events exactly at T. Show damage at useful encounter windows and a cumulative curve/table when rankings depend on time. A sustained magazine model may use n*d/((n-1)*shot_interval+reload+next_cycle_delay), but define the cycle so firing intervals are neither omitted nor double-counted. Prefer an event timeline for finite windows.

Buffs: assign each effect a documented stacking category; apply max, sum, product, caps or exclusions only where verified for this patch. A generic multiplication of every listed percent is invalid. Include weapon perks, surges, empowerment, debuffs, activity bonuses, enemy scalars, ability scalars and team duplication restrictions only if they apply to that component. Treat enhanced perks and catalysts as their measured effects, not automatic damage upgrades.

Expected shot damage with misses and crits can be p_hit * (p_crit_given_hit*d_crit + (1-p_crit_given_hit)*d_body). Correlated failures, kill requirements and threshold effects need explicit event/state modeling rather than multiplying average uptime by every effect. Distinguish baseline, optimistic ceiling and realistic rotation; calculate sensitivity to accuracy, proc uptime, range and boss movement.

## Survival, ability loops and PvP

- For independently stacking DR factors r_i, remaining damage factor is product(1-r_i), and DR=1-product(1-r_i). Use only after verifying independence, caps, affected damage types and activity rules. EHP=HP/remaining_factor is meaningful for that damage type and state; model overshields, healing timing, gates, invulnerability and resistance separately.
- Obtain actual current stat curves and breakpoints; never assume every armor era uses 0-100, ten-point tiers or the same stat names. Evaluate marginal gains under the applicable system, including caps and diminishing returns.
- Track cooldowns, charges, flat energy grants, cooldown/energy scalars, refunds, internal cooldowns, orbs/pickups, kills and travel time. Verify feedback-loop causality and steady-state resource balance. An ability cannot fund its own first activation without an external initial resource.
- PvP: calculate discrete shots/bursts to defeat the specified health/overshield/DR, then timing from first hit to lethal hit; include charge time separately where relevant. Use per-shot rounding and range falloff when supported. Report accuracy/crit requirements and resilience/health breakpoints rather than only an average DPS.
- Keep add-clear, champion control, team support, mobility, ease of execution and survival as distinct objectives. Compare Pareto-efficient choices. Do not call a glass-cannon DPS maximum universally best.

## Reproducibility

For a substantial comparison generate a small Python calculation or spreadsheet in the working project with input values, units, source URLs and patch metadata. Reject nonfinite or impossible inputs. Check meaningful invariants: no buffs yields baseline; no ammo yields no weapon damage; mutually exclusive effects never stack; cumulative damage does not decrease; larger windows do not delete prior events; no free energy enters a loop. Test thresholds and reload boundaries. Do not fill missing measurements with plausible-looking numbers.

Output a compact common-scenario table: damage by window, total ammo damage, resource cost, survival/utility, conditions and confidence. Report percentage difference against a named baseline and identify break-even windows/uptimes. Preserve reasonable precision; measured uncertainty should constrain significant digits. If only symbolic comparison is supported, show the formula and required measurement instead of a numeric winner.
