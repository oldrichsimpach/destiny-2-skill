"""Fingerprint permitted local snapshots; flag changed claims/results without adopting values."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlparse
from engine_common import ROOT, load, emit, cli_error
from aegis import scalar


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,default=scalar,allow_nan=False).encode()).hexdigest()


def sha_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def snapshot(path,source_id):
    p=Path(path);result=dict(schema_version=1,source_id=source_id,sha256=sha_file(p),
        acquired_utc=dt.datetime.now(dt.timezone.utc).isoformat(),kind=p.suffix.lower(),sheets={})
    if p.suffix.lower()=='.xlsx':
        import openpyxl
        f=openpyxl.load_workbook(p,data_only=False,keep_links=False)
        v=openpyxl.load_workbook(p,data_only=True,keep_links=False)
        for sheet in f:
            cells={}
            for row in sheet:
                for c in row:
                    cached=v[sheet.title][c.coordinate].value
                    if c.value is None and cached is None and c.comment is None:continue
                    # Rich text distinctions can encode PvE/PvP or obsolete/struck-out entries.
                    style=str(c._style) if c.has_style else None
                    cells[c.coordinate]=digest(dict(value=c.value,cached=cached,type=c.data_type,
                        comment=c.comment.text if c.comment else None,hyperlink=c.hyperlink.target if c.hyperlink else None,
                        style=style,font=str(c.font),fill=str(c.fill),alignment=str(c.alignment),number_format=c.number_format))
            result['sheets'][sheet.title]=dict(visibility=sheet.sheet_state,rows=sheet.max_row,columns=sheet.max_column,
                merges=sorted(str(x) for x in sheet.merged_cells.ranges),cells=cells)
        f.close();v.close()
    elif p.suffix.lower() in ('.sqlite','.db'):
        with sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True) as db:
            result['metadata']=dict(db.execute('SELECT key,value FROM metadata'))
            for kind in ['DestinyInventoryItemDefinition','DestinyPlugSetDefinition']:
                cells={str(h):hashlib.sha256(body.encode()).hexdigest() for h,body in db.execute('SELECT hash,body FROM definitions WHERE kind=?',(kind,))}
                result['sheets'][kind]=dict(cells=cells)
    else:raise ValueError('Snapshot requires a permitted XLSX or manifest SQLite file')
    return result


def in_range(cell,area):
    from openpyxl.utils.cell import range_boundaries, coordinate_to_tuple
    try:
        left,top,right,bottom=range_boundaries(area.replace('$',''))
        row,col=coordinate_to_tuple(cell)
        return (left is None or col>=left) and (right is None or col<=right) and (top is None or row>=top) and (bottom is None or row<=bottom)
    except (ValueError,TypeError):return True # Unknown locator syntax invalidates conservatively.


def impacted_claims(changes,source_id,ledger,structural=None):
    affected=[];structural=set(structural or [])
    for claim in ledger['records']:
        provenance=claim['provenance']
        if provenance['source_id']!=source_id:continue
        watches=provenance.get('watch')
        if not watches:
            locator=provenance.get('locator','')
            watches=[dict(sheet=locator.split('!',1)[0].strip("'"),range=locator.split('!',1)[1])] if '!' in locator else []
        if not watches:
            if changes or structural:affected.append(claim['id'])
            continue
        if any(w['sheet'] in structural or any(in_range(cell,w['range']) for cell in changes.get(w['sheet'],[])) for w in watches):
            affected.append(claim['id'])
    return sorted(affected)


def affected_results(paths,claim_ids,manifest_changed=False):
    output=[]
    for path in paths:
        result=load(path)
        used=set(result.get('evidence_used',{}))
        for row in result.get('results',[]):used.update(row.get('evidence_used',{}))
        intersection=sorted(used & set(claim_ids))
        if intersection or (manifest_changed and result.get('manifest')):
            output.append(dict(path=str(path),status='needs_review',claims=intersection,
                               reason='dependency changed; no result automatically recomputed or approved'))
    return output


def diff(old,new,ledger,results=()):
    if old['source_id']!=new['source_id'] or old['kind']!=new['kind']:raise ValueError('Snapshot source/type mismatch')
    changes={};structural=[]
    for name in sorted(set(old['sheets'])|set(new['sheets'])):
        a=old['sheets'].get(name);b=new['sheets'].get(name)
        if a is None or b is None:
            structural.append(name);changes[name]=sorted((a or b)['cells']);continue
        if {k:v for k,v in a.items() if k!='cells'}!={k:v for k,v in b.items() if k!='cells'}:structural.append(name)
        changed=[key for key in set(a['cells'])|set(b['cells']) if a['cells'].get(key)!=b['cells'].get(key)]
        if changed:changes[name]=sorted(changed)
    affected=impacted_claims(changes,new['source_id'],ledger,structural)
    changed=old['sha256']!=new['sha256']
    return dict(source_id=new['source_id'],file_changed=changed,status='needs_review' if changed else 'unchanged',
        semantic_changes=bool(changes or structural),structural_sheets=structural,
        changed_cell_counts={s:len(v) for s,v in changes.items()},changed_cell_sample={s:v[:50] for s,v in changes.items()},
        affected_claims=affected,affected_results=affected_results(results,affected,changed and new['kind'] in ('.sqlite','.db')),
        note='Whole-file differences can be export metadata only. Semantic differences and references need review; no coefficients or patch applicability are changed.')


def patch_review(document,ledger,results=()):
    parsed=urlparse(document['url'])
    if parsed.scheme!='https' or not (parsed.hostname=='bungie.net' or (parsed.hostname or '').endswith('.bungie.net')):
        raise ValueError('Patch evidence must identify an official HTTPS Bungie source')
    if not document.get('patch') or not document.get('published_at'):raise ValueError('Patch id and publication date required')
    text=re.sub(r'[^a-z0-9]+',' ',document['text'].casefold())
    affected=[]
    for claim in ledger['records']:
        names=[claim['entity']]+claim.get('aliases',[])
        if any((' '+re.sub(r'[^a-z0-9]+',' ',name.casefold()).strip()+' ') in ' '+text+' ' for name in names):affected.append(claim['id'])
    return dict(patch=document['patch'],url=document['url'],status='needs_review' if affected else 'no_named_claim_match',
        affected_claims=sorted(affected),affected_results=affected_results(results,affected),
        note='Conservative mention matching is a review aid, not semantic proof of a mechanics change. Renames or generic changes can be missed; read the complete official notes. No applicability automatically extended.')


def update_review_state(report,path):
    state=load(path) if Path(path).exists() else dict(schema_version=1,claims={})
    for key in report['affected_claims']:
        state['claims'][key]=dict(status='needs_review',reason=report.get('url') or report.get('source_id'),
            detected_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    emit(state,path)


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    s=sub.add_parser('snapshot');s.add_argument('file');s.add_argument('--source-id',required=True);s.add_argument('--out',required=True)
    s=sub.add_parser('diff');s.add_argument('old');s.add_argument('new');s.add_argument('--ledger');s.add_argument('--result',action='append',default=[]);s.add_argument('--out');s.add_argument('--state')
    s=sub.add_parser('patch');s.add_argument('file');s.add_argument('--ledger');s.add_argument('--result',action='append',default=[]);s.add_argument('--out');s.add_argument('--state')
    a=p.parse_args()
    def run():
        if a.command=='snapshot':return snapshot(a.file,a.source_id)
        ledger=load(a.ledger or ROOT/'data/claims.json')
        report=diff(load(a.old),load(a.new),ledger,a.result) if a.command=='diff' else patch_review(load(a.file),ledger,a.result)
        if a.state:update_review_state(report,a.state)
        return report
    cli_error(p,lambda:emit(run(),a.out))


if __name__=='__main__':main()
