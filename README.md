# Destiny 2 Skill 0.4-beta.1 — EXPERIMENTÁLNÍ BETA

Skill pro výzkum Destiny 2, kontrolu vybavení a matematické porovnání buildů pro konkrétní patch a situaci. Nová beta implementuje všech šest navržených oblastí v níže uvedeném rozsahu. **Stále nejde o úplný simulátor hry ani plně ověřený solver všech legálních loadoutů.**

## Co přibylo

| Oblast | Implementace | Praktický výsledek |
|---|---|---|
| Evidence a rozpory | 82 záznamů s jednotkou, komponentou, patchem, podmínkami a původem. | Neznámý patch, rozporná varianta nebo nekompatibilní jednotka se nepoužije tiše ve výpočtu. |
| Boss Damage a munice | Nová XLSX čtečka, přesné řádky s hlavičkami/vzorci/komentáři; index 6 026 řádkových lokací včetně variant. | Přístup k baseline hodnotám, týmovým rotacím, boss kontextu a konkrétní ammo economy. |
| Kontrola kombinací | Přesný item hash, socket/pool, class, slot a equipping unique labels; volitelné auditované subclass/artifact/mod pravidlo. | Rozliší reedice zbraní a zachová neověřené serverové podmínky jako neznámé. |
| Časová simulace | Charge/recovery, reloady, swapy, projektily/ticky, buff intervaly, procy a finite ammo/refilly. | Damage za konkrétní okno a okamžiky změny pořadí variant. |
| Přežití a ability loopy | Typované příchozí útoky, DR skupiny, overshield vrstvy, healing; energie, cooldowny, CES/CMS a refundy. | Výkon lze porovnat spolu s přežitím a bilancí zdrojů. |
| Změny zdrojů | Fingerprint buněk/vzorců/komentářů/formátování, manifest diff, review patchů a blokace zneplatněných claimů. | Změna podkladu označí závislé výpočty k revizi; nové koeficienty se automaticky neschvalují. |

Navíc: profily přesnosti, pohybu a doloženého range falloff; seeded Monte Carlo pro nelineární hit procy; konečné candidate-set/Pareto porovnání s volitelným omezením na přesné vlastněné instance. Utility a náboje různých typů se nesčítají do umělého univerzálního skóre.

## Ověřené příklady

V syntetickém příkladu dá burst varianta za 10 sekund 600 jednotek, sustained varianta 720. Po přidání pohybového okna sustained klesne na 540 a pořadí se otočí. Na vzdálenějším profilu se změní podle zadaného falloff. Příchozí poškození zároveň ukončí další akce v okamžiku smrti; již vystřelené projektily mohou dopadnout.

Ability příklad správně aplikuje grant `0,4 × 0,5 = 0,2` a zachová bilanci `počáteční energie + pasivní regen + granty − spotřeba = konečná energie`. První cast si nemůže zaplatit sám. **Tato čísla jsou demonstrační a nepředstavují konkrétní Destiny build.**

Skutečný manifest rozlišil starší a novější Hezen Vengeance: příklad Cluster Bomb + Elemental Honing je strukturálně podporovaný pro novější hash `2265407516`, ne pro starší `4050645223` ve stejných socketech. Pozitivní výstup stále znamená pouze `structurally_compatible_runtime_unverified` pro uvedený manifest snapshot.

## Zdroje a přesnost

[Aegis Endgame Analysis](https://docs.google.com/spreadsheets/d/1JM-0SlxVDAi-C6rGVlLxa-J1WGewEeL8Qvq4htWZHhY/edit) zůstává hlavním komunitním zdrojem pro kontext endgame PvE voleb. [Aegis Boss Damage](https://docs.google.com/spreadsheets/d/1_5wtBjRYHHxuF4oJKDb_iOGZs-wTkzB6RYbnyNLbuz4/edit) doplňuje damage/rotace/bossy; Data Compendium mechaniky; Court stackování; Mossy munici; specializované statové zdroje ability loopy. Bungie a konkrétní verze itemů určují aplikovatelnost změn a pravidel.

Zůstává audit všech 52 Endgame listů a jeho index. Nová evidence zahrnuje 47 porovnaných archetypových baseline hodnot; 46 odpovídalo zaokrouhlení. Precision Scout zůstává nevyřešený rozpor 75,298 vs 79,14239363. U Rewind Rounds se nejistota `1? s` nepřepisuje na potvrzenou sekundu. Courtův subset má nadále vlastní omezení na 9.7.0.3. U nových baseline hodnot se zachovávají patche jednotlivých zdrojových řádků.

## Instalace a použití

Zkopíruj složku `destiny-2` do osobního adresáře Codex `skills`. Vyvolej `$destiny-2`. Nové matematické/manifest nástroje používají standardní Python; XLSX čtečky a fingerprinty potřebují `openpyxl`.

Veřejný balíček obsahuje integraci, metadata, faktické subsety a indexy. Plné cizí sešity nejsou zrcadlené, protože nebyla doložena licence k jejich redistribuci. Stáhni originály přes povolené Download ovládání a importuj je. Místní instalace zadavatele obsahuje jeho povolené exporty Endgame, Boss Damage a reserves. Velký manifest zůstává samostatně mimo balíček.

Z adresáře skillu:

```sh
python scripts/evidence.py conflicts
python scripts/workbooks.py boss import /cesta/boss-damage.xlsx
python scripts/workbooks.py boss search "Hezen"
python scripts/workbooks.py reserves import /cesta/reserves.xlsx
python scripts/legality.py examples/manifest-roll-example.json --db /cesta/manifest.sqlite
python scripts/simulate.py examples/encounter-demo.json --out comparison.json
python scripts/simulate.py examples/stochastic-proc-demo.json --summary
python scripts/optimize.py examples/encounter-demo.json --out frontier.json
```

Příklad požadavku: `$destiny-2 Porovnej doložené rotace pro 10s a 20s fázi. Ověř konkrétní verze zbraní, uveď neznámé podmínky, ukaž dopad horší přesnosti a pohybu a zachovej rozpory ve zdrojích.`

Podrobné kontrakty: [simulace](destiny-2/references/simulation.md), [evidence a legalita](destiny-2/references/evidence-and-legality.md), [Boss Damage](destiny-2/references/boss-damage.md), [kontrola změn](destiny-2/references/updates.md).

## Validace a hranice

Prošlo 64 funkčních testů a nezávislá behaviorální kontrola. Ověřeny byly také skutečné manifest pooly, čtení S29 Fireteam řádku včetně array formula a vytvoření fingerprintů originálních exportů. Podrobnosti: [VALIDATION.md](VALIDATION.md).

Výsledek může být syntetický, podmíněný nebo založený na scoped evidenci. Monte Carlo dává odhady a kvantily, nikoli přesnou pravděpodobnost. U ensemble výstupu jsou resource/effect traces výslovně z trialu 0. Unknown podmínky, engine frame pravidla, úplné cooldown/stat křivky, všechny perk interakce, nepopsané AI útoky, serverové equip restrikce a globální optimalizace všech buildů zůstávají mimo ověřený rozsah. Komunitní datum aktualizace nenahrazuje kontrolu patche nebo herní měření.

Čtečky originály nemění a výpočty nic ve hře nevybavují. Automatická invalidace sleduje claim reference; volně zadané číselné předpoklady vyžadují ruční revizi. Pravidelný monitor se konfiguruje místně a není součástí veřejného ZIPu jako samospouštěcí služba.

[Changelog](CHANGELOG.md) · [Pokrytí](COVERAGE.md) · [Releases](https://github.com/oldrichsimpach/destiny-2-skill/releases)

Zásluhy za původní výzkum patří Aegisovi, Courtovi, Destiny Data Compendiu, Mossymu, Engineeeerovi, Clarity a dalším uvedeným autorům. Neoficiální projekt; Destiny 2 patří Bungie.

