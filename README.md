# Destiny 2 Skill v0.2 — EXPERIMENTÁLNÍ

**Druhá experimentální verze — Pre-release.** Skill pomáhá Codexu dohledávat Destiny 2 informace a sestavovat doložené matematické porovnání pro konkrétní sandbox, vybavení a aktivitu. Základem zůstává vydaná v0.1.

## Co přibylo

| Obsah | Rozsah |
|---|---|
| Buffy, debuffy a surgy | 15 vybraných záznamů s hodnotami, PvE/PvP rozlišením, kategorií stackování, aktivací a podmínkami. Ne všechny efekty mají změřené trvání. |
| Další fakta | 24 záznamů: perk timing, konkrétní rozpory ve starém generátoru, oficiální změny a jejich podmínky. |
| Statové vzorky | 102 záznamů pro šest statových hodnot: 0,50,70,100,150,200. Nejde o všechny křivky; null zůstává neznámé/nepoužitelné. |
| Pokrytí zdrojů | 15 auditovaných položek, rozdělených na ověřené v daném rozsahu, částečné, zastaralé, nedostupné a nezpracované. |
| Živé testy | Damage Generator a Armor Planner: baseline, změna relevantního vstupu, navazující přepočet a reset. |
| Pomocné nástroje | Lokální vyhledávání dat, standardní stackování, porovnání explicitních damage událostí a read-only inspekce povolených XLSX exportů. |

`destiny-2/` je instalovatelný skill. Lokální pracovní podklady a původní exporty tabulek nejsou součástí repozitáře ani ZIPu. Balíček obsahuje skill, README, přehled pokrytí, testovací souhrn, VERSION a .gitignore.

## Co skill prakticky umí

- Vyhledat uložený efekt či statový vzorek a uvést zdroj, jednotku, podmínky a omezení.
- Pro podporované standardní efekty spočítat nejvyšší empowerment/debuff/same-element surge v každé kategorii a součin mezi kategoriemi.
- Rozlišit Radiant od Well, Deadfall od Moebius a nepřičítat jednotlivé úrovně surge k sobě.
- Spočítat damage a DPS ze zadaného časového rozvrhu zásahů s přesností a poměrem crit/body, včetně podmíněně aktivních efektů.
- Posoudit, zda se pořadí variant mění podle délky fáze a setupu. Demonstrační scénář používá syntetické jednotky a není doporučením konkrétní zbraně.
- Vypočítat EHP pro explicitně nezávislé DR faktory stejného typu a stavu.
- Zkontrolovat exportované tabulky: skryté listy, dropdowny, vzorce, cached hodnoty, chyby a neportabilní Google funkce.
- Používat původní nástroj v0.1 pro veřejný Bungie manifest; stávající velká databáze zůstává mimo balíček.

## Doložené výsledky výzkumu

Ve starém Damage Generatoru je Radiant 25 %, generic Tether 30 % a Banner Shield 40 %. Novější Courtův přehled uvádí pro kontrolovaný sandbox Radiant 20 %, Deadfall 35 % a Banner Shield 25 %. Záznamy zůstávají oddělené. Generátor lze ovládat a jeho vzorce se přepočítávají, ale tím se jeho staré koeficienty nestávají současnými.

Courtův přehled sám deklaruje kontrolu proti 9.7.0.3. Nepodařilo se načíst úplné poznámky .3/.4; jejich obsah proto netvrdíme jako ověřený. Hodnoty Courtova subsetu jsou označené jako **částečně ověřené a uzamčené na 9.7.0.3**. Pomocný nástroj odmítne jejich tiché použití jako 9.7.0.6. Nejde o plošné potvrzení dnešního sandboxu.

Exotic Class Item Planner je označený jako neudržovaný, Prismatic Planner vrací smazaný soubor, PvP Chart varuje před nepřesnostmi při aktualizaci a Mossyho scaling sheet před zastaralou částí obsahu. Celý [přehled pokrytí](COVERAGE.md) rozlišuje konkrétní ověřený rozsah.

## Použití

Zkopíruj složku `destiny-2` do osobního adresáře Codex `skills`. Vyvolej ji jako `$destiny-2` a u porovnání zadej pokud možno class, aktivitu, encounter, časové okno a dostupné vybavení.

Příklady:

> `$destiny-2 Ověř, jestli lze pro dnešní build použít hodnoty z Damage Generatoru. Uveď konkrétní rozpory a chybějící ověření.`

> `$destiny-2 Porovnej dvě doložené rotace za 10 a 20 sekund. Zohledni setup, reloady, buff uptime a potřebné zásahy.`

Samostatné nástroje, spuštěné z adresáře `destiny-2`:

```sh
python scripts/knowledge.py search Radiant
python scripts/knowledge.py stat --value 100
python scripts/knowledge.py stack --ids radiant well surge-3 tractor --mode PvE --sandbox 9.7.0.3 --allow-partial
python scripts/compare.py examples/conditional-comparison.json
python scripts/science_workbook.py permitted-export.xlsx --range 'Database!B4:C5' --source-url SOURCE_URL
```

První čtyři příkazy používají standardní knihovnu Pythonu. Poslední potřebuje `openpyxl`. Příkaz stack je výslovně podmíněný výpočet částečně ověřeného historického subsetu, nikoli hotový současný build. Popis vstupního kontraktu najdeš v `destiny-2/references/calculations.md`.

## Testy a omezení

Skill prošel validátorem. Prošlo 12 funkčních testů pro stackování, PvE/PvP rozdíly, nesoulad sandboxů, neověřená data, reload/časové hranice, pravděpodobnosti, DR a skutečné přepočty a reset dvou tabulek. Nezávislá behaviorální kontrola ověřila, že ze zastaralého generátoru nevzniká deklarace aktuálního nejlepšího buildu. Podrobnosti jsou v [testovacím souhrnu](VALIDATION.md).

**Stále chybí** kompletní databáze všech efektů a historických patchů, všechny perk interakce, každá statová křivka a ability-specific chunk scalar, úplný solver legálních loadoutů, automatická simulace ability loopů a kompletně přetestované aktuální damage baselines pro všechny zbraně a encountery. Výpočetní nástroj zpracuje dodaná data; jejich pravdivost, legalitu a aktuálnost musí agent ověřit ze zdrojů.

Veřejné originály nebyly upraveny. Dvě vytvořené pracovní kopie zůstávají soukromé a testované vstupy jsou resetované. Externí importy a Apps Script nebyly autorizovány ani spuštěny.

## Zdroje

Číselná komunitní data jsou výsledkem práce autorů, zejména [Courta](https://destiny2.science/court-sheet), [Destiny Data Compendia](https://destiny2.science/data-compendium) a [Engineeeera](https://destiny2.science/armor-stat-planner). Rozcestník: [Destiny Science](https://www.destiny2.science/). Každý uložený záznam obsahuje konkrétní source ID a locator; oficiální změny pocházejí od [Bungie](https://www.bungie.net/7/en/News).

[Clarity](https://www.d2clarity.com/) je externí zdroj pro další výzkum; jeho databáze není v tomto balíčku zrcadlená. [Podmínky využití](https://www.d2clarity.com/partnerships), [zpětná vazba k tooltipům](https://d2clarity.com/discord).

Neoficiální projekt. Destiny 2 a související herní obsah patří Bungie. Tento skill si nepřisvojuje autorství cizích měření ani práva k původním tabulkám.

