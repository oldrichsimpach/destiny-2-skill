# Destiny 2 Skill 0.3-beta.1 — EXPERIMENTÁLNÍ BETA

Skill pro Codex pomáhá dohledat Destiny 2 informace, sestavit legální build a porovnat varianty pro konkrétní patch, aktivitu a situaci. **Jde o průběžnou experimentální betu, nikoli kompletní encyklopedii nebo univerzální simulátor.**

Hlavním komunitním zdrojem pro pokryté endgame PvE oblasti je nyní [Aegis — Destiny 2: Endgame Analysis](https://docs.google.com/spreadsheets/d/1JM-0SlxVDAi-C6rGVlLxa-J1WGewEeL8Qvq4htWZHhY/edit?gid=1062099834#gid=1062099834). Bylo zpracováno všech 52 exportovaných listů včetně skrytých: struktura, vzorce, komentáře, metadata aktualizací, původ dat a omezení. Obsah nebyl plošně ověřen měřením ve hře. Datum stažení 2026-11-01 není datum platnosti každého čísla.

## Co přibylo a k čemu to je

- Průvodce Aegis zdrojem a přehled všech listů s rozlišením historického, ignorovaného a hypotetického obsahu.
- Čtečka originálního XLSX: vyhledávání zbraní/perků a dalších položek, podrobné vyhledání v obsahu, konkrétní řádky včetně hlaviček, vzorců a komentářů, kontrola zdroje pomocí SHA-256.
- Offline index názvů a přesných řádků. Bez originálu nevrací vymyšlené hodnoty efektů.
- Kontrola základních vztahů RPM a cyklického DPS vůči uloženým výsledkům; zvláštní případy a rozpory se hlásí. Čtečka nepřepočítává celý Excel.
- Pravidla pro kombinování doporučení s ověřením legálních rollů, aktuálních Bungie změn a specializovaných pravidel stackování. Dva doporučené perk sloupce automaticky netvoří pár a S tier není společná jednotka napříč zbraněmi.

Zůstávají nástroje v0.2 pro manifest, 15 vybraných buffů/debuffů/surgů, 24 číselných faktů, 102 statových vzorků, podmíněné stackování, explicitní damage události a EHP. Jejich původní patchová omezení zůstávají platná. Nový sešit je automaticky nepřepisuje.

## Instalace a použití

Zkopíruj adresář `destiny-2` do svého osobního adresáře Codex `skills`. Vyvolej `$destiny-2`. Pro práci s XLSX je potřeba Python a `openpyxl`; index funguje se standardním Pythonem.

Originální sešit není veřejně zrcadlen v repozitáři ani ZIPu: nebyla dohledána licence k šíření jeho plné kopie. V dokumentu zvol File → Download → Microsoft Excel, poté z adresáře skillu:

```sh
python scripts/aegis.py import /cesta/k/originalu.xlsx
python scripts/aegis.py search "Cascade Point" --sheet Perks
python scripts/aegis.py row --sheet Perks 19
python scripts/aegis.py sheets
python scripts/aegis.py math-check
```

Místní instalace zadavatele obsahuje jeho staženou kopii. Veřejný balíček obsahuje vlastní integraci, metadata a index s odkazem na originál. Podrobnosti jsou v [průvodci](destiny-2/references/aegis.md) a [auditu listů](destiny-2/references/aegis-audit.md).

Příklad: `$destiny-2 Najdi vhodné zbraně pro tento encounter, ověř konkrétní roll a porovnej je v 10s a 25s fázi. Odděl damage, přežití a utility; uveď patch, zdroje a chybějící měření.`

## Omezení a původ

Chybí úplný historický archiv, všechna čísla a interakce, všechny legální loadouty a současné měřené baselines pro každý encounter. Zdrojové tier listy jsou autorská doporučení. Encounters není databáze HP bossů; ignorované armor/build listy nejsou dnešní doporučení. Živé změny vyžadují ověření. Import je ruční a změna souboru vyžaduje nový audit.

[Changelog](CHANGELOG.md) · [Validace](VALIDATION.md) · [GitHub releases](https://github.com/oldrichsimpach/destiny-2-skill/releases)

Za zdrojový výzkum patří zásluhy Aegisovi, Destiny Data Compendiu, Courtovi a dalším autorům uvedeným u jednotlivých dat. Neoficiální projekt; Destiny 2 patří Bungie. Skill si nepřisvojuje původní tabulky ani měření.
