"""Search curated evidence and combine explicitly supported effect categories."""
import argparse
import datetime as dt
import json
import math
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data'


def read(name):
    return json.loads((DATA / name).read_text(encoding='utf-8-sig'))


def effect_multiplier(ids, mode, sandbox, allow_partial=False):
    if mode not in ('PvE', 'PvP'):
        raise ValueError('Mode must be PvE or PvP')
    catalog = read('effects.json')
    records = {r['id']: r for r in catalog['records']}
    groups, sources = {}, []
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate effect IDs')
    for key in ids:
        if key not in records:
            raise ValueError('Unknown effect: ' + key)
        record = records[key]
        if sandbox != record['sandbox']:
            raise ValueError('Sandbox mismatch for ' + key + '; revalidate rather than relabel data')
        if record['status'] != 'verified_for_scope' and not allow_partial:
            raise ValueError('Partially verified data requires --allow-partial: ' + key)
        if mode not in record['bonus']:
            raise ValueError('Mode not measured for ' + key)
        group = record['stacking_group']
        if group not in ('empowering', 'global_debuff', 'weapon_surge'):
            raise ValueError('Unsupported stacking category: ' + group)
        amount = record['bonus'][mode]
        if not math.isfinite(amount) or amount < 0:
            raise ValueError('Invalid bonus')
        groups.setdefault(group, []).append((key, 1 + amount))
        sources.append({'id': key, 'source_id': record['source_id'], 'locator': record['locator'],
                        'conditions': record['conditions'], 'status': record['status']})
    chosen = {group: {'id': max(values, key=lambda x: x[1])[0],
                      'factor': max(v for _, v in values),
                      'suppressed': [key for key, _ in values if key != max(values, key=lambda x: x[1])[0]]}
              for group, values in groups.items()}
    return {'multiplier': math.prod(g['factor'] for g in chosen.values()), 'groups': chosen,
        'mode': mode, 'sandbox': sandbox, 'evidence': sources,
        'scope': 'weapon damage only; externally satisfied triggers; same-element surges; no special overrides',
        'warning': 'A numeric factor does not prove loadout legality, proc uptime or current-patch validity.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    search = sub.add_parser('search')
    search.add_argument('text')
    stack = sub.add_parser('stack')
    stack.add_argument('--ids', nargs='+', required=True)
    stack.add_argument('--mode', choices=['PvE', 'PvP'], required=True)
    stack.add_argument('--sandbox', required=True)
    stack.add_argument('--allow-partial', action='store_true')
    stats = sub.add_parser('stat')
    stats.add_argument('--value', type=int, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'stack':
            result = effect_multiplier(args.ids, args.mode, args.sandbox, args.allow_partial)
        elif args.command == 'stat':
            data = read('stat-samples.json')
            result = [r for r in data['records'] if r['stat_value'] == args.value]
            if not result:
                raise ValueError('No measured sample at that value; interpolation is not implemented')
        else:
            query = args.text.casefold()
            result = []
            for file in ('effects.json', 'facts.json', 'stat-samples.json', 'coverage.json'):
                for row in read(file)['records']:
                    if query in json.dumps(row, ensure_ascii=False).casefold():
                        result.append({'dataset': file, 'record': row})
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError) as exc:
        parser.exit(1, str(exc) + '\n')


if __name__ == '__main__':
    main()
