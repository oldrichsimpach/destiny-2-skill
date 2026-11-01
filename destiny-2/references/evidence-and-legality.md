# Evidence, conflicts and structural loadout checks

## Evidence ledger

`data/claims.json` adds explicitly scoped observations. Existing v0.2 data remain preserved in their original datasets; the ledger is a bounded additional layer, not a silent replacement.

```sh
python scripts/evidence.py search "Precision"
python scripts/evidence.py conflicts
```

A claim contains id, entity, field, numeric value or unknown, unit, PvE/PvP mode, component scope, exact `applies_to` sandbox IDs, conditions and provenance (source URL, locator, retrieval date, optional snapshot SHA and watched ranges). `independence_group` records source lineage. Two Aegis workbooks can be consistent without providing independent confirmation.

Resolution rejects unknown/hypothetical values, incompatible units/components/modes, missing conditions and unestablished patch applicability. Partially verified/community/conflicted/historical records need explicit `allow_partial`; that flag never bypasses the patch gate. Conflicts need `conflict_choices:{"group":"claim-id"}` and remain conditional. Source metadata supplied by a caller does not independently validate a measurement.

Precision Scout has an unresolved 75.298 vs 79.14239363 observation. Endgame's effective patch is not established, so that variant cannot be used numerically for an arbitrary sandbox merely by selecting it. Rewind Rounds retains DDC's `1?` as unknown rather than coercing it to a one-second lockout. Historical Generator values are scoped to its legacy model, not a current patch.

Persisted source-change invalidations in `assets/private/review-state.json`, or a scenario's explicit `review_state` path, block later ledger use of `needs_review` claims. Review source evidence, update applicability/snapshot and deliberately clear the reviewed entry after validation; a changed file does not automatically approve new coefficients.

## Exact versions and sockets

```sh
python scripts/legality.py examples/manifest-roll-example.json --db /absolute/path/manifest.sqlite
```

`class_type` uses the manifest enum (0 Titan, 1 Hunter, 2 Warlock). Each selection uses exact `item_hash`, and optional `plugs:[{"socket":3,"plug_hash":"hash","path":"random_roll"}]`. Pin `manifest_version` for a reproducible snapshot. Names alone are insufficient for reissues. The snapshot's retrieval date is not its effective sandbox.

The checker uses [Bungie's socket definition](https://bungie-net.github.io/multi/schema_Destiny-Definitions-DestinyItemSocketEntryDefinition.html), plug sets, class restrictions, equipment slot and equipping unique labels. It rejects duplicate slot occupation, incompatible classes, recipe hashes masquerading as gear and duplicate unique-label groups. It distinguishes new theoretical rolls from owned equipment. Static membership and currentlyCanRoll are evidence about a snapshot's pool, not complete proof of drop availability or simultaneous server insertion rules.

Supported plug paths:

- `random_roll`: that exact socket's randomized plug set; false currentlyCanRoll rejects a theoretical new roll.
- `reusable`: declared reusable plugs/set; dynamic insertion remains unknown.
- `crafting`: associated recipe socket's reusable set; levels/materials/unlocks remain unknown.
- `initial`: only that socket's initial plug, not an inferred random pool.
- `owned`: normalized supplied runtime evidence of the selected active/enabled plug. This can establish a historical owned plug even if today's random set differs.

Owned evidence uses `owned_instance:{item_hash,item_instance_id,provenance,retrieved_at,sockets:{"3":{plug_hash,is_enabled}}}`. Import runtime evidence deliberately from a user-authorized export; the tool does not authenticate to Bungie or equip anything. It does not automatically turn raw API fields into this normalized schema.

Successful checks return `structurally_compatible_runtime_unverified`; contradictions return `invalid`, and individual missing checks remain `unknown`. Server restrictions, disabled items, activities, all cross-socket restrictions and actual ownership cannot be certified from a static manifest. **Do not describe the positive structural result as a fully verified legal build.**

## Subclasses, artifact and mod budgets

An optional audited rule pack must pin sandbox, class and provenance. It declares `max_aspects`, aspects with allowed subclass IDs and fragment slot counts, complete fragment pools by subclass, and optional artifact ID/mod costs/budget/prerequisites. The loadout's subclass selections, artifact identity, duplicate mods, prerequisites, fragment capacity and supplied armor-mod energy budgets are checked against it.

Optional `armor.slots` provides per-slot `energy_capacity` and `socket_count`; `armor.mods` provides `allowed_slots`, authoritative `energy_cost` and `max_copies`. These override inconsistent caller costs/capacities. Missing definitions leave slot/copy eligibility unknown. Artifact mod rules may also declare `excludes` IDs.

Unknown membership remains unknown; it is not converted into invalid just because a partial source omits it. Only label a pool complete when its source establishes completeness. The generic rule engine does not contain every live Destiny subclass/Prismatic/armor restriction. The synthetic test pack demonstrates constraints and is not a production game-rule dataset.

For real requests obtain the exact versioned manifest and applicable rules. Verify crafting/enhancement, catalysts, subclass exclusivity, artifact era and activity restrictions independently where the checker reports unknown. Historical gear in today's sandbox needs today's applicable equip/mechanics rules; a historical performance request needs contemporary evidence.
