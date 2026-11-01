"""Compare a finite candidate set, optionally constrained to declared owned instances."""
import argparse
import copy
from contextlib import closing
from engine_common import load, emit, cli_error
from simulate import evaluate
from legality import Manifest, validate


def optimize(scenario,inventory=None,manifest=None,rules=None,ledger=None):
    selected=[];excluded=[];checks={}
    owned={}
    if inventory is not None:
        for item in inventory['instances']:
            key=str(item['item_instance_id'])
            if key in owned:raise ValueError('Duplicate inventory instance id')
            owned[key]=str(item['item_hash'])
    for build in scenario['builds']:
        reason=None;loadout=build.get('loadout')
        if inventory is not None:
            if not loadout or not loadout.get('items'):reason='No concrete instance loadout to verify against inventory'
            else:
                for selection in loadout['items']:
                    instance=selection.get('owned_instance',{}).get('item_instance_id') or selection.get('item_instance_id')
                    if owned.get(str(instance))!=str(selection['item_hash']):
                        reason='Required exact item instance/hash is not in supplied inventory';break
        if manifest is not None and loadout is not None:
            checks[build['name']]=validate(loadout,manifest,rules)
            if checks[build['name']]['status']=='invalid':reason='Structural loadout checks failed'
        else:checks[build['name']]={'status':'not_checked','reason':'No concrete loadout/manifest supplied'}
        if reason:excluded.append(dict(name=build['name'],reason=reason))
        else:selected.append(build)
    if not selected:return dict(candidates=[],excluded=excluded,legality=checks,status='no eligible supplied candidates')
    s=copy.deepcopy(scenario);s['builds']=selected
    result=evaluate(s,ledger);fronts=[]
    profiles=sorted({r['profile'] for r in result['results']})
    for profile in profiles:
        rows=[r for r in result['results'] if r['profile']==profile]
        include_survival=all(r['survival'] is not None and not r.get('ensemble') for r in rows)
        include_probability=all(r.get('ensemble',{}).get('survival_probability') is not None for r in rows)
        def objectives(r):
            values=[w['expected_damage'] for w in r['windows']]
            if include_survival:values.append(r['survival']['time_alive'])
            if include_probability:values.append(r['ensemble']['survival_probability'])
            return values
        frontier=[]
        for row in rows:
            current=objectives(row)
            dominated=False
            for other in rows:
                if other is row:continue
                values=objectives(other)
                if all(a>=b for a,b in zip(values,current)) and any(a>b for a,b in zip(values,current)):
                    dominated=True;break
            if not dominated:frontier.append(row['name'])
        fronts.append(dict(profile=profile,pareto_front=frontier,
            objectives=['expected damage at '+str(w['seconds'])+' s' for w in rows[0]['windows']]
                +(['time alive'] if include_survival else [])+(['survival probability'] if include_probability else []),
            final_window_ranking=[r['name'] for r in sorted(rows,key=lambda r:r['windows'][-1]['expected_damage'],reverse=True)]))
    return dict(frontiers=fronts,excluded=excluded,legality=checks,comparison=result,
        scope='Optimum only within supplied candidates and declared scenarios. Manifest-compatible is not server-verified legal. Utility and ammo types are not collapsed into arbitrary weighted scores.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('scenario');p.add_argument('--inventory');p.add_argument('--db');p.add_argument('--rules');p.add_argument('--ledger');p.add_argument('--out')
    a=p.parse_args()
    def run():
        kwargs=dict(inventory=load(a.inventory) if a.inventory else None,rules=load(a.rules) if a.rules else None,ledger=load(a.ledger) if a.ledger else None)
        if a.db:
            with closing(Manifest(a.db)) as m:return optimize(load(a.scenario),manifest=m,**kwargs)
        return optimize(load(a.scenario),**kwargs)
    cli_error(p,lambda:emit(run(),a.out))


if __name__=='__main__':main()
