"""Read an explicitly downloaded Aegis XLSX; never execute or recalculate it."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data' / 'aegis-source.json'
SNAPSHOT = ROOT / 'assets' / 'private' / 'aegis-endgame-analysis.xlsx'


def scalar(value):
    return value.isoformat() if isinstance(value, (datetime.datetime, datetime.date)) else value


def book(path, cached=True):
    try:
        import openpyxl
    except ImportError:
        raise ValueError('Install openpyxl to read XLSX. The bundled index needs only Python.')
    return openpyxl.load_workbook(path, data_only=cached, read_only=False, keep_links=False)


def inventory(w):
    statuses = {}
    for row in w['Status'].iter_rows(min_row=2, max_row=37, values_only=True):
        statuses[row[0]] = {'author_updated': scalar(row[1]), 'author_status': row[2]}
    out = []
    for s in w:
        st = statuses.get(s.title.replace(' (ignore)', ''), {})
        reason = ('historical' if s.sheet_state != 'visible' or '(old' in s.title or 'outdated' in s.title
                  else 'excluded_by_author' if '(ignore)' in s.title
                  else 'hypothetical' if st.get('author_status') == 'future'
                  else 'editorial_history' if s.title == 'Changelog'
                  else 'metadata' if s.title == 'Status' else 'candidate')
        out.append(dict(sheet=s.title, visibility=s.sheet_state, rows=s.max_row,
                        columns=s.max_column, classification=reason,
                        eligible=reason == 'candidate', **st))
    return out


def label(s, r):
    cols = ([3, 4] if s.title == 'Archetypes' else [2, 3] if s.title == 'Encounters'
            else [3, 5, 6] if s.title == 'Set Bonuses' else [2, 3] if s.title == 'Artifact Mods'
            else [3] if s.title in ('Shopping List', 'Exotic Weapons') else [2])
    return ' | '.join(str(s.cell(r, c).value) for c in cols if s.cell(r, c).value is not None)


def row_data(w, wf, name, r):
    s, f = w[name], wf[name]
    header_row = 1 if name in ('Shopping List', 'Status') else 2
    if not 1 <= r <= s.max_row:
        raise ValueError('Row outside worksheet')
    return {'sheet': name, 'row': r, 'cells': {
        s.cell(r, c).column_letter: dict(header=scalar(s.cell(header_row, c).value),
            header_comment=f.cell(header_row, c).comment.text if f.cell(header_row, c).comment else None,
            value=scalar(s.cell(r, c).value),
            formula=f.cell(r, c).value if f.cell(r, c).data_type == 'f' else None,
            comment=f.cell(r, c).comment.text if f.cell(r, c).comment else None)
        for c in range(1, s.max_column + 1)
        if s.cell(r, c).value is not None or f.cell(r, c).value is not None}}


def check_math(w):
    """Independently check applicable basic arithmetic against exported caches."""
    checks, skipped, failures = [], [], []
    s = w['Archetypes']
    for r in range(3, s.max_row + 1):
        vals = {c: s[f'{c}{r}'].value for c in ['H','M','O','P','Q','S','AI']}
        for target, inputs, calc in [('O', ['M'], lambda: 60 / vals['M']),
                                     ('AI', ['H','P','Q','S'], lambda: vals['H']*vals['P']/(vals['Q']+vals['S']))]:
            # These are standard-row relationships, not sword/heat-specific formulas.
            if not all(isinstance(vals[c], (int, float)) for c in inputs) or s[f'C{r}'].value == 'Sword':
                skipped.append(f'{target}{r}')
                continue
            try:
                expected = calc()
                actual = s[f'{target}{r}'].value
                if not isinstance(actual, (int,float)):
                    skipped.append(f'{target}{r}')
                    continue
                ok = abs(actual-expected) <= max(1e-5, abs(expected)*1e-7)
                checks.append({'cell': f'{target}{r}', 'expected': expected, 'cached': actual, 'matches': ok})
                if not ok:
                    failures.append(checks[-1])
            except ZeroDivisionError:
                skipped.append(f'{target}{r}')
    return dict(checks=checks, skipped=skipped, mismatches=failures,
                limitation='Cache arithmetic check only. No Excel/Sheets recalculation or in-game baseline validation; special formulas can differ.')


def run(args):
    source = json.loads(SOURCE.read_text(encoding='utf-8'))
    if args.command == 'import':
        p = Path(args.file).resolve()
        if p.suffix.lower() != '.xlsx':
            raise ValueError('Use a downloaded .xlsx export')
        w = book(p)
        required = {'Status','Archetypes','Perks','Shopping List','Origin Traits'}
        if not required <= set(w.sheetnames):
            raise ValueError('This does not match the expected Endgame Analysis workbook')
        if w['Perks']['B2'].value != 'Name' or w['Archetypes']['C2'].value != 'Weapon':
            raise ValueError('Unexpected schema; review before importing')
        SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        if p != SNAPSHOT.resolve():
            shutil.copy2(p, SNAPSHOT)
        digest = hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest()
        return dict(installed=str(SNAPSHOT), sha256=digest, matches_audited_snapshot=digest == source['sha256'],
                    note='A changed workbook needs a fresh audit. Live queries read its Status; bundled index remains the audited snapshot.')
    p = Path(args.workbook) if args.workbook else SNAPSHOT
    if not p.exists():
        if args.command == 'search':
            idx = json.loads((ROOT/'data'/'aegis-index.json').read_text(encoding='utf-8'))
            hits = [x for x in idx if args.query.casefold() in x['name'].casefold()
                    and (not args.sheet or x['sheet'] == args.sheet)
                    and (args.include_history or x['eligible'])]
            return dict(source=source['url'], snapshot_available=False, index_only=True,
                        audited_at=source['retrieved_at'], results=hits[:args.limit], total=len(hits),
                        note='Index has names and locators only. Download original XLSX and import it for effects/formulas.')
        if args.command == 'sheets':
            return dict(snapshot_available=False, sheets=source['sheets'])
        raise ValueError('No local workbook. Download XLSX from the source and run import FILE.')
    w = book(p)
    inv = inventory(w)
    provenance = dict(url=source['url'], sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                      audited_snapshot=hashlib.sha256(p.read_bytes()).hexdigest() == source['sha256'],
                      warning='Author dates are not effective sandbox versions. Cached values are not recalculated.')
    if args.command == 'sheets':
        return dict(source=provenance, sheets=inv)
    if args.command == 'math-check':
        return dict(source=provenance, **check_math(w))
    selected = [s for s in inv if not args.sheet or s['sheet'] == args.sheet]
    if args.sheet and not selected:
        raise ValueError('Unknown sheet')
    eligible = [s for s in selected if args.include_history or s['eligible']]
    if args.command == 'row':
        if not eligible:
            raise ValueError('Sheet excluded by default. Use --include-history for explicitly labeled archival research.')
        return dict(source=provenance, status=eligible[0], **row_data(w, book(p, False), args.sheet, args.row))
    hits = []
    for meta in eligible:
        s = w[meta['sheet']]
        for r in range(3 if s.title != 'Shopping List' else 2, s.max_row + 1):
            name = label(s, r)
            hay = ' '.join(str(c.value) for c in s[r] if c.value is not None) if args.details else name
            if args.query.casefold() in hay.casefold():
                hits.append(dict(name=name, sheet=s.title, row=r, status=meta))
    return dict(source=provenance, total=len(hits), results=hits[:args.limit])


def main():
    # Windows legacy console encodings cannot represent all source symbols.
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('import').add_argument('file')
    for command in ['sheets','search','row','math-check']:
        p = sub.add_parser(command)
        p.add_argument('--workbook')
        if command in ('search','row'):
            p.add_argument('--sheet', required=command == 'row')
            p.add_argument('--include-history', action='store_true')
        if command == 'search':
            p.add_argument('query')
            p.add_argument('--details', action='store_true')
            p.add_argument('--limit', type=int, default=20)
        if command == 'row':
            p.add_argument('row', type=int)
    try:
        print(json.dumps(run(parser.parse_args()), ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError) as e:
        parser.exit(2, f'{e}\n')


if __name__ == '__main__':
    main()
