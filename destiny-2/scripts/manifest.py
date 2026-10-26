"""Versioned public Destiny manifest cache and raw definition lookup."""
import argparse
from contextlib import closing
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import urllib.request

BASE = 'https://www.bungie.net'


def fetch(url):
    headers = {'User-Agent': 'DestinyKnowledgeSkill/1.0'}
    if os.environ.get('BUNGIE_API_KEY'):
        headers['X-API-Key'] = os.environ['BUNGIE_API_KEY']
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as r:
        return json.load(r)


def sync(cache):
    envelope = fetch(BASE + '/Platform/Destiny2/Manifest/')
    if envelope.get('ErrorCode') != 1 or 'Response' not in envelope:
        raise ValueError('Manifest API unsuccessful: ' + str(envelope.get('ErrorStatus')))
    manifest = envelope['Response']
    version = manifest['version']
    tables = manifest['jsonWorldComponentContentPaths']['en']
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / ('manifest-' + hashlib.sha256(version.encode()).hexdigest()[:20] + '.sqlite')
    if target.exists():
        print(target.resolve())
        return
    # Unique temp file avoids colliding with another download; only publish on success.
    import tempfile
    fd, temp_name = tempfile.mkstemp(prefix='manifest-', suffix='.partial', dir=cache)
    os.close(fd)
    temp = Path(temp_name)
    try:
        with closing(sqlite3.connect(temp)) as db, db:
            db.execute('CREATE TABLE definitions (kind TEXT, hash TEXT, name TEXT, body TEXT, PRIMARY KEY(kind,hash))')
            db.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)')
            for kind, path in sorted(tables.items()):
                if not path.startswith('/') or path.startswith('//'):
                    raise ValueError('Unexpected manifest content path')
                records = fetch(BASE + path)
                if not isinstance(records, dict):
                    raise ValueError('Unexpected component format: ' + kind)
                db.executemany('INSERT INTO definitions VALUES (?,?,?,?)', (
                    (kind, str(h), v.get('displayProperties', {}).get('name', ''), json.dumps(v, ensure_ascii=False))
                    for h, v in records.items()))
                print(kind, len(records), flush=True)
            meta = {'version': version, 'retrieved_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                    'source': BASE + '/Platform/Destiny2/Manifest/', 'language': 'en',
                    'components': json.dumps(sorted(tables))}
            db.executemany('INSERT INTO metadata VALUES (?,?)', meta.items())
            db.execute('CREATE INDEX names ON definitions(kind,name)')
        temp.replace(target)
    finally:
        if temp.exists():
            temp.unlink()
    print(target.resolve())


def lookup(args):
    if not args.db.is_file():
        raise ValueError('Snapshot does not exist')
    with closing(sqlite3.connect(args.db.resolve().as_uri() + '?mode=ro', uri=True)) as db:
        meta = dict(db.execute('SELECT key,value FROM metadata'))
        if args.command == 'get':
            row = db.execute('SELECT body FROM definitions WHERE kind=? AND hash=?', (args.table, args.hash)).fetchone()
            if row is None:
                raise ValueError('Definition not found in this snapshot')
            result = json.loads(row[0])
        else:
            # instr gives literal substring matching, without LIKE wildcard surprises.
            params = (args.table, args.text)
            clause = 'kind=? AND instr(lower(name),lower(?))>0'
            total = db.execute('SELECT count(*) FROM definitions WHERE ' + clause, params).fetchone()[0]
            rows = db.execute('SELECT hash,name FROM definitions WHERE ' + clause + ' ORDER BY name,hash LIMIT ?', params + (args.limit,)).fetchall()
            result = {'total_matches': total, 'returned': len(rows), 'matches': [{'hash': h, 'name': n} for h, n in rows]}
        print(json.dumps({'metadata': meta, 'result': result}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    cmd = commands.add_parser('sync')
    cmd.add_argument('--cache', type=Path, required=True)
    for name in ('search', 'get'):
        cmd = commands.add_parser(name)
        cmd.add_argument('--db', type=Path, required=True)
        cmd.add_argument('--table', default='DestinyInventoryItemDefinition')
        if name == 'search':
            cmd.add_argument('--text', required=True)
            cmd.add_argument('--limit', type=int, default=30, choices=range(1, 1001), metavar='1..1000')
        else:
            cmd.add_argument('--hash', required=True)
    args = parser.parse_args()
    try:
        sync(args.cache) if args.command == 'sync' else lookup(args)
    except (ValueError, OSError, sqlite3.Error, KeyError) as exc:
        parser.exit(1, 'Error: ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
