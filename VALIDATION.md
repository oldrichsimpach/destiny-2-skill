# Ověření experimentální v0.2

Ověření dokončeno 2026-10-27 před publikací v0.2. Původní v0.1 a databáze manifestu zůstaly zachované.

## Živé kalkulačky

Testy proběhly v Google Sheets v nových soukromých pracovních kopiích. Exporty zachytily navazující výsledky z původního výpočetního enginu. Lokální openpyxl sloužilo pouze ke čtení vzorců a cached hodnot.

### Damage Generator v3.1

| Stav | Database B4 | B5 | C5 | B8 | L15 | AV15 |
|---|---:|---:|---|---|---:|---:|
| Baseline | 20 | 30 | false | false | 39 074 | 586 110 |
| Vlastní fáze | 45 | 45 | true | false | 39 074 | 742 406 |
| Zapnuté existující buffy | 45 | 45 | true | true | 63 495,25 | 1 206 409,75 |
| Reset | 20 | 30 | false | false | 39 074 | 586 110 |

L15 se změnilo přesně o faktor 1,625 = 1,30 × 1,25, protože zdroj obsahuje Tether a staré Radiant hodnoty. To ověřuje výpočetní cestu, **nikoli současnou platnost** tohoto násobiče nebo základního fusion damage. Zvolena byla výchozí adaptive Fusion Rifle, bez dodatečných perků a za zdrojových podmínek PoH - Zulmak.

Při prvním zadání vznikla neplatná textová hodnota v C5. Byla zjištěna kontrolou exportu, opravena a test zopakován. Úspěšné hodnoty výše pocházejí z opraveného běhu. Při resetu se zvlášť ověřilo false oproti prázdné buňce.

### Armor Planner - MoT

| Stav | Build Planner D14 | F2 Health | F4 Grenade | M3 orb HP | M10 grenade cooldown scalar | M11 energy bonus |
|---|---|---:|---:|---:|---:|---:|
| Baseline | +10 Grenade | 25 | 55 | 17,5 | 2,037055610 | 0,7227715407 |
| Změna modu | +10 Health | 35 | 45 | 24,5 | 1,742105105 | 0,5272284593 |
| Reset | +10 Grenade | 25 | 55 | 17,5 | 2,037055610 | 0,7227715407 |

První volný vstup začínající `+10` způsobil parse error. Finální změna i reset byly potvrzeny výběrem existující dropdown položky. Chybové exporty nebyly použity jako numerický zdroj. M10 je faktor vůči zdrojovému zero-stat baseline, ne automaticky vůči historickému cooldownu. Úplná nezávislá validace křivek ve hře nebyla provedena.

## Lokální nástroje

- Validátor skill-creator: úspěšný.
- 12 unittest testů: úspěšné.
- Maximum empowermentu, debuffu a surge po kategoriích; Radiant+Well se nesčítají.
- Rozdílné PvE/PvP koeficienty; odmítnutí nepodloženého režimu.
- Odmítnutí částečných dat bez explicitního opt-in a odmítnutí nesouladu sandboxů efektů i damage baseline.
- Munice, reload a `[0,T)` hranice; pravděpodobnost zásahu/crit; zákaz neplatných/nonfinite vstupů.
- EHP pro nezávislé DR; invulnerability vyžaduje jiný model.
- Read-only inspekce reálného povoleného exportu: zachovaný SHA-256, hidden sheets, vzorce vs cache, neportabilní Google funkce a omezené rozsahy.
- Automatická kontrola reálných before/after/reset exportů obou testovaných kalkulaček.

## Nezávislá behaviorální kontrola

Scénář požadoval aktuální solo boss damage ze staršího generátoru s Radiant, Well, třemi surgy a Tractorem. Skill vedl k podmíněnému historickému weapon multiplieru 1,9825, nikoli k falešnému současnému absolutnímu damage nebo vítěznému buildu.

Kontrola upozornila, že ručně zadaná stará baseline se nedá automaticky rozpoznat podle volného popisu. Přidali jsme povinné `baseline_sandbox` a `baseline_kind`, kontrolu souladu a test. Jde stále o prohlášení volajícího, nikoli nezávislou validaci zdroje.

## Neověřeno

Kompletní 9.7.0.3/.4 patch chain, aktuálnost všech ostatních koeficientů, všechny zbraně/rotace, legální inventory loadouty, externí importy, Apps Script, grafy a všechny skryté závislosti. Ostatní zdroje mají svůj skutečný rozsah kontroly v COVERAGE.md a data/coverage.json. Ukázkový event scénář používá syntetické damage jednotky.

