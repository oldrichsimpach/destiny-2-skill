"""Read permitted Boss Damage/ammo snapshots with row-level provenance."""
import argparse
import hashlib
from pathlib import Path
import shutil
import datetime as dt
from aegis import book, scalar
from engine_common import ROOT, load, emit, cli_error, integer, finite


def catalog():return load(ROOT/'data/workbooks.json')


def snapshot(source_id, path=None):
    records = catalog()['sources']
    if source_id not in records:raise ValueError('Unknown workbook source')
    meta = records[source_id]
    p = Path(path) if path else ROOT/meta['local_path']
    if not p.is_file():raise ValueError('Download the permitted XLSX and import it first: '+meta['url'])
    return meta, p


def sheet_status(s):
    historic = s.sheet_state != 'visible' or any(x in s.title.lower() for x in ['old','historical','backup','testing','copy of'])
    return {'sheet':s.title,'visibility':s.sheet_state,'rows':s.max_row,'columns':s.max_column,
            'eligible':not historic,'classification':'archival_or_experimental' if historic else 'candidate_requires_context'}


def describe(source_id, path=None):
    m,p=snapshot(source_id,path);w=book(p)
    return dict(source=m['url'],sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                audited_snapshot=hashlib.sha256(p.read_bytes()).hexdigest()==m['sha256'],
                sheets=[sheet_status(s) for s in w],
                warning='New file identity requires a new audit. Sheet visibility is not patch validation.')


def row(source_id, sheet, number, path=None, include_history=False):
    m,p=snapshot(source_id,path);w=book(p);wf=book(p,False)
    if sheet not in w.sheetnames:raise ValueError('Unknown worksheet')
    s,f=w[sheet],wf[sheet];status=sheet_status(s)
    if not status['eligible'] and not include_history:raise ValueError('Archival/experimental sheet needs --include-history')
    integer(number,'row',1,s.max_row)
    header=m.get('header_rows',{}).get(sheet,1)
    cells={}
    for c in s[number]:
        fc=f[c.coordinate]
        if c.value is None and fc.value is None and not fc.comment:continue
        h=f.cell(header,c.column)
        cells[c.column_letter]=dict(header=scalar(s.cell(header,c.column).value),value=scalar(c.value),
            formula=scalar(fc.value) if fc.data_type=='f' else None,comment=fc.comment.text if fc.comment else None,
            header_comment=h.comment.text if h.comment else None,struck_out=bool(fc.font.strike))
    sha=hashlib.sha256(p.read_bytes()).hexdigest()
    receipts_path=ROOT/'assets/private/workbook-receipts.json'
    receipts=load(receipts_path) if receipts_path.exists() else {}
    retrieved=m['retrieved_at'] if sha==m['sha256'] else receipts.get(sha,{}).get('retrieved_at','unknown')
    return dict(source_id=source_id,url=m['url'],sheet=sheet,row=number,status=status,cells=cells,
                sha256=sha,audited_snapshot=sha==m['sha256'],retrieved_at=retrieved,
                warning='Cached values, not a recalculation. Preserve target, units, setup, buffs and patch before use.')


def search(source_id, query, path=None, details=False, include_history=False, limit=20):
    meta=catalog()['sources'][source_id]
    p=Path(path) if path else ROOT/meta['local_path']
    if not p.exists():
        entries=[r for r in load(ROOT/'data/workbook-index.json') if r['source_id']==source_id and query.casefold() in r['name'].casefold()]
        return dict(index_only=True,total=len(entries),results=entries[:limit],warning='Names/locators only. No effect or rotation data available without original.')
    w=book(p);hits=[]
    for s in w:
        if not sheet_status(s)['eligible'] and not include_history:continue
        cols=meta.get('label_columns',{}).get(s.title,[])
        if not cols and not details:continue
        header=meta.get('header_rows',{}).get(s.title,1)
        for r in range(header+1,s.max_row+1):
            label=' | '.join(str(s.cell(r,c).value).split('\n')[0] for c in cols if s.cell(r,c).value is not None)
            hay=' '.join(str(c.value) for c in s[r] if c.value is not None) if details else label
            if query.casefold() in hay.casefold():hits.append(dict(source_id=source_id,sheet=s.title,row=r,name=label,status=sheet_status(s)))
    return dict(index_only=False,total=len(hits),results=hits[:limit],sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def baseline(source_id,sheet,number,column,component,path=None):
    if source_id!='boss' or sheet!='Weapons' or column not in ('L','T'):
        raise ValueError('Only Weapons L visual-normalized / T healthbar-normalized baselines supported; other models need manual interpretation')
    r=row(source_id,sheet,number,path)
    value=r['cells'].get(column,{}).get('value')
    finite(value,'baseline',0)
    patch=r['cells'].get('U',{}).get('value')
    if not isinstance(patch,str) or not patch:raise ValueError('No source measurement patch in column U')
    name=' / '.join(str(r['cells'].get(c,{}).get('value','')) for c in ('B','C'))
    return dict(id=f'boss-weapons-{number}-{column.lower()}-{component}',entity=name,field='normalized damage observation',
        value=value,unit='aegis_normalized_damage',mode='PvE',components=[component],status='partially_verified',
        applies_to=[patch],conditions=['verify original measurement unit (shot, burst, pellet or combined event)',
            'verify source target normalization and listed modifiers']+([] if r['audited_snapshot'] else ['verify new snapshot identity and schema'])
            +([] if r['retrieved_at']!='unknown' else ['verify source retrieval date']),
        provenance=dict(source_id='boss',url=r['url'],locator=f'Weapons!{column}{number}',audited_snapshot=r['audited_snapshot'],
            snapshot_sha256=r['sha256'],retrieved_at=r['retrieved_at'],measurement_patch=patch,
            watch=[dict(sheet='Weapons',range=f'A{number}:X{number}'),dict(sheet='Weapons',range='A1:X2')]),
        independence_group='aegis',notes='Component label supplied by caller. This helper does not certify measurement semantics or portability to another patch.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',choices=['boss','reserves']);p.add_argument('--workbook')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('sheets')
    s=sub.add_parser('search');s.add_argument('query');s.add_argument('--details',action='store_true');s.add_argument('--include-history',action='store_true');s.add_argument('--limit',type=int,default=20)
    s=sub.add_parser('row');s.add_argument('sheet');s.add_argument('number',type=int);s.add_argument('--include-history',action='store_true')
    s=sub.add_parser('baseline');s.add_argument('sheet');s.add_argument('number',type=int);s.add_argument('column',choices=['L','T']);s.add_argument('--component',required=True,choices=['weapon_impact','weapon_explosion','weapon_combined'])
    s=sub.add_parser('import');s.add_argument('file');s.add_argument('--retrieved-at')
    a=p.parse_args()
    def run():
        if a.command=='sheets':return describe(a.source,a.workbook)
        if a.command=='search':return search(a.source,a.query,a.workbook,a.details,a.include_history,a.limit)
        if a.command=='row':return row(a.source,a.sheet,a.number,a.workbook,a.include_history)
        if a.command=='baseline':return baseline(a.source,a.sheet,a.number,a.column,a.component,a.workbook)
        meta=catalog()['sources'][a.source];src=Path(a.file)
        if src.suffix.lower()!='.xlsx':raise ValueError('Only permitted XLSX exports accepted')
        w=book(src)
        if not set(meta['required_sheets'])<=set(w.sheetnames):raise ValueError('Workbook identity/schema mismatch')
        for check in meta['identity_cells']:
            if w[check['sheet']][check['cell']].value!=check['value']:raise ValueError('Unexpected header schema')
        if a.retrieved_at:
            try:dt.date.fromisoformat(a.retrieved_at)
            except ValueError:raise ValueError('--retrieved-at must be an explicit YYYY-MM-DD date')
        dest=ROOT/meta['local_path'];dest.parent.mkdir(parents=True,exist_ok=True)
        if src.resolve()!=dest.resolve():
            if dest.exists() and hashlib.sha256(src.read_bytes()).hexdigest()!=hashlib.sha256(dest.read_bytes()).hexdigest():
                history=dest.parent/'history';history.mkdir(parents=True,exist_ok=True)
                backup=history/(a.source+'-'+hashlib.sha256(dest.read_bytes()).hexdigest()+'.xlsx')
                if not backup.exists():shutil.copy2(dest,backup)
            shutil.copy2(src,dest)
        receipt_path=ROOT/'assets/private/workbook-receipts.json'
        receipts=load(receipt_path) if receipt_path.exists() else {}
        receipts[hashlib.sha256(dest.read_bytes()).hexdigest()]=dict(source_id=a.source,
            imported_at=dt.datetime.now(dt.timezone.utc).isoformat(),retrieved_at=a.retrieved_at or 'unknown')
        emit(receipts,receipt_path)
        return describe(a.source)
    cli_error(p,lambda:emit(run()))


if __name__=='__main__':main()
