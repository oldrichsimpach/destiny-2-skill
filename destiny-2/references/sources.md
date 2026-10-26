# Sources, identity and historical evidence

## Source map

These are discovery entry points, not evidence that every page or value is current. Check the specific resource's effective version and cite the actual record/tab/article.

| Need | Starting source | Use and limitation |
|---|---|---|
| Patch changes, official announcements, disabled content | https://www.bungie.net/7/en/News and https://help.bungie.net/ | Bungie is primary evidence for announced changes; stated percentages still need the correct baseline and later hotfixes. |
| Item identity, static stats, sockets, plug sets, activities, records, objectives, lore | https://bungie-net.github.io/ and https://www.bungie.net/Platform/Destiny2/Manifest/ | Official schema and public manifest; definitions omit many hidden numbers and acquisition conditions. |
| Hidden perk/ability numbers and test methodology | https://www.destiny2.science/ | Follow links to Destiny Data Compendium, Clarity, Court's damage stacking, Aegis Boss Damage/Endgame Analysis, Mossy's scaling/reserves and ability energy studies. These are community measurements, not official statements. |
| Weapon rolls and item lookup | https://www.light.gg/ and https://www.d2foundry.gg/ | Cross-check exact reissue, sockets, enhanced perks and calculated stats; popularity is not mathematical optimality. |
| Perk explanations | https://www.d2clarity.com/ | Find underlying measurement, version and PvE/PvP applicability. |
| Historical lore and text | https://www.ishtar-collective.net/ | Distinguish fiction, interpretation and playable mechanics. |
| Puzzles, secrets and discoveries | https://www.reddit.com/r/raidsecrets/ | Leads requiring independent confirmation, reproduction and patch checks. |
| Removed pages and older rules | https://web.archive.org/ plus dated Bungie notes, source revision history and contemporary tests | An archived page proves what was published then, not necessarily an effective game change on the capture date. |

The official API schema and Destiny Science directory were inspected on 2026-10-24. This is a source-routing check, not a freshness certification for their data. If a resource is unavailable, report the gap and use independently supported alternatives rather than inventing its content.

## Evidence record

For material numerical claims collect: entity name and hash/reissue, field/value/unit, PvE/PvP mode, effective patch/date or interval, retrieval date, direct URL, author/test method, target and activity/power baseline, sample size where known, confidence and caveats. Keep source text separate from computed results. Preserve contradictory measurements until their conditions are reconciled.

For a historical statement identify the last supported old behavior, first supported new behavior and any gap. Unknown dates stay unknown. Do not combine isolated values across patches to create a build that never existed.

## Weapon pools and catalogs

Resolve DestinyInventoryItemDefinition and its socket entries against DestinyPlugSetDefinition using randomizedPlugSetHash, reusablePlugSetHash, reusablePlugItems and singleInitialItemHash where present. Retain socket index and flags. Distinguish a definition pool, live-instance available plugs and an equipped/enabled plug. Check SocketPlugSources and the official schema when resolving live account components.

Potential plugs alone do not prove legal combinations: verify column exclusivity, intrinsic/frame, origin trait, adept variant, enhanced/crafted rules, quest stages, perk unlock requirements and era. Mark legacy fixed rolls, sunset/reprised versions, unclassified definitions and unavailable drops separately. A catalog may include removed content only if surviving definitions or historical sources support it. Do not claim the latest manifest contains every item ever released.

For all-encompassing requests enumerate categories and produce a coverage report (present/missing, date range, source, unresolved gaps). Expand by task-relevant batches. Store normalized facts and citations in a user-authorized project/cache; do not silently alter this skill or scrape entire third-party sites without regard for their access rules. Account credentials are unnecessary for public knowledge; use an authorized account integration only when the user asks about their own inventory.
