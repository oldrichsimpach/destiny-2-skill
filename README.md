# Destiny 2 Skill — v0.1 EXPERIMENTAL

> **První experimentální verze.** Projekt je v rané fázi a jeho pokrytí dat není kompletní. Výsledky závisí na dostupných zdrojích, jejich aktuálnosti a správně zadaných podmínkách. Verze 0.1 není hotová encyklopedie všech čísel ani automatický simulátor celé hry.

## K čemu skill slouží

Skill rozšiřuje Codex o postupy a nástroje pro výzkum Destiny 2. Pomáhá dohledávat současné i historické informace, sestavovat buildy a porovnávat jejich výkon podle doložených hodnot a konkrétní aktivity. Je určen hráčům, kteří chtějí rozumět tomu, proč kombinace funguje, za jakých podmínek a kde přestává být výhodná.

Odpovídá v jazyce uživatele a zachovává anglické názvy herních prvků pro snadné dohledání.

## Co verze 0.1 obsahuje

- `SKILL.md`: instrukce pro výzkum, rozlišení verzí hry, práci se zdroji a sestavování odpovědí.
- `references/sources.md`: mapa zdrojů a pravidla pro ověřování předmětů, perk poolů, historických změn a důvěryhodnosti dat.
- `references/modeling.md`: metodika výpočtů damage, DPS, PvP TTK, přežití, cooldownů, buffů a podmínek aktivace.
- `references/activities.md`: postupy pro výzkum aktivit, encounterů, nepřátel, získávání odměn a secretů.
- `references/data.md`: návod k použití lokální databáze a vysvětlení jejího pokrytí.
- `scripts/manifest.py`: nástroj v Pythonu pro stažení veřejného anglického Bungie manifestu, uchovávání verzovaných SQLite snapshotů, hledání podle názvu a výpis definic podle hashe.
- `agents/openai.yaml`: metadata pro zobrazení a vyvolání skillu v Codexu.

## Co s ním lze dělat

Prostřednictvím Codexu a dostupných výzkumných nástrojů skill pomáhá:

- Dohledávat zbraně, armory, perky, traity, katalyzátory, schopnosti, aspekty, fragmenty a modifikace.
- Ověřovat konkrétní verze předmětů a legální kombinace perků. Stejnojmenné reissue nemusí mít stejný perk pool.
- Rozlišovat historický výkon předmětu od jeho fungování v dnešním sandboxu.
- Navrhovat buildy pro konkrétní class, aktivitu, encounter a dostupné vybavení.
- Připravovat doložené výpočty a srovnání damage za společné časové okno, spotřeby munice, přežití a schopností.
- Zohledňovat stackování buffů a debuffů, aktivaci perků, přesnost, pohyb cíle, reloady a další podmínky, pokud jsou příslušná pravidla ověřena.
- Dohledávat mechaniky aktivit, výskyt nepřátel, získávání vybavení, exotické mise a potvrzené secrety.
- Uvádět zdroje, předpoklady a mezery v datech. Pokud chybí měření, má nabídnout podmíněný nebo symbolický výpočet místo vymyšlených čísel.

## Co zatím chybí

- Kompletní předem naplněná databáze všech buffů, debuffů, jejich hodnot, trvání, výjimek a vzájemného stackování.
- Úplné tabulky statových křivek, skrytých koeficientů, interních cooldownů a energetických návratů pro všechny verze hry.
- Kompletní archiv všech historických perk poolů a mechanik přiřazených ke konkrétním patchům.
- Hotový automatický simulátor rotací a optimalizátor všech možných buildů.
- Úplné ověření každé aktivity, nepřítele, odměny a secretu napříč historií.

Bungie manifest obsahuje definice a vztahy mezi herními prvky. Sám o sobě neposkytuje všechna skrytá čísla, celou historii ani potvrzení, že je obsah právě dostupný. Výzkumné instrukce nejsou totéž co již zpracovaná a ověřená databáze těchto hodnot.

## Instalace a použití

Zkopíruj složku `destiny-2` do osobního adresáře `skills` v Codexu. Skill vyvolej jako `$destiny-2`.

Příklady zadání:

- `$destiny-2 Porovnej dva Hunter buildy pro solo dungeon. Dolož hodnoty, spočítej damage za 20 sekund a zohledni přežití i spolehlivost aktivace.`
- `$destiny-2 Ověř, jaké perky může mít tato konkrétní verze zbraně a které lze kombinovat.`
- `$destiny-2 Vysvětli stackování buffů v tomto buildu. Uveď patch, zdroje a co se zatím nepodařilo ověřit.`

Pro stažení manifestu použij Python 3 a příkaz z kořenové složky repozitáře:

```sh
python destiny-2/scripts/manifest.py sync --cache ./d2-cache
```

Nástroj vypíše cestu k vytvořené databázi. Příklady vyhledávání najdeš v `destiny-2/references/data.md`. Skript používá standardní knihovnu Pythonu; případný požadavek Bungie na API klíč řeší proměnná `BUNGIE_API_KEY`. Vygenerovaná databáze není součástí vydání. Nové snapshoty nevytvoří zpětně chybějící historická data.

## Stav vydání

**v0.1 — první experimentální vydání:** základ výzkumného skillu, metodika matematických porovnání a nástroj pro veřejný manifest. Pokrytí se má rozšiřovat podle doložených dat a praktického ověřování. Nejde o záruku optimálního buildu pro každou situaci.

Neoficiální komunitní projekt. Destiny 2 je majetkem Bungie. Odkazované komunitní zdroje patří jejich autorům.
