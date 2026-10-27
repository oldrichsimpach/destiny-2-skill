# Public manifest cache

Python 3 standard library only. Run from the skill directory, choosing a writable cache outside the installed skill:

```powershell
python scripts/manifest.py sync --cache 'C:/path/to/project/d2-cache'
python scripts/manifest.py search --db 'C:/path/to/project/d2-cache/SNAPSHOT.sqlite' --text 'Gjallarhorn'
python scripts/manifest.py search --db 'C:/path/to/project/d2-cache/SNAPSHOT.sqlite' --table DestinyActivityDefinition --text 'Prophecy'
python scripts/manifest.py get --db 'C:/path/to/project/d2-cache/SNAPSHOT.sqlite' --table DestinyInventoryItemDefinition --hash 123456
```

`sync` prints the actual snapshot path; use that path instead of the illustrative SNAPSHOT filename. Downloads every component offered by the current English JSON manifest, one at a time. It can take minutes and substantial disk space. Files are immutable snapshots; reuse of the same version prints its existing path. If Bungie requires an API key, supply `BUNGIE_API_KEY` in the environment without printing it. There is no OAuth or account mutation.

Search results are capped and explicitly report matches returned and total matches. Search is name substring matching, not exhaustive semantic retrieval. `get` returns raw JSON for a hash, including sockets and references to other definitions. Use further `get` calls to resolve plug sets. IDs are text to preserve unsigned hashes. Metadata includes retrieval timestamp, manifest version and source. A manifest version is not a game patch identifier.

The first sync captures only the public manifest available now. Keeping later snapshots creates history from that point forward; it cannot reconstruct missing older versions, historical hidden mechanics, encounter scripts, secret solutions or numerical perk behavior. Source those separately using sources.md. Never advertise the cache as a complete historical knowledge base.

