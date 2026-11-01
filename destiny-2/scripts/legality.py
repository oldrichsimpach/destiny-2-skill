"""Tri-state, exact-hash manifest/socket checks. Never claims full server equipability."""
import argparse
from contextlib import closing
from pathlib import Path
import sqlite3
from engine_common import load, emit, integer, cli_error, unique


class Manifest:
    def __init__(self,path):
        self.db=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)
        self.metadata=dict(self.db.execute('SELECT key,value FROM metadata'))

    def get(self,kind,key):
        row=self.db.execute('SELECT body FROM definitions WHERE kind=? AND hash=?',(kind,str(key))).fetchone()
        if not row:return None
        import json
        return json.loads(row[0])

    def close(self):self.db.close()


def validate(document, manifest, rules=None):
    checks=[]
    def add(status,scope,message,**extra):checks.append(dict(status=status,scope=scope,message=message,**extra))
    cls=integer(document['class_type'],'class_type',0,2)
    purpose=document.get('purpose','theoretical_roll')
    if purpose not in ('theoretical_roll','owned_equipment'):raise ValueError('Invalid validation purpose')
    expected=document.get('manifest_version')
    if expected and expected!=manifest.metadata.get('version'):
        add('unknown','snapshot','Requested manifest version differs from available snapshot')
    if not expected:add('unknown','snapshot','No manifest version pinned; this is a dated snapshot check')
    buckets={};labels={};instances=set()
    items=document.get('items',[])
    if not items:add('unknown','equipment','No item selections supplied')
    for selection in items:
        key=str(selection['item_hash']);item=manifest.get('DestinyInventoryItemDefinition',key)
        if not item or item.get('redacted'):
            add('unknown',key,'Item definition missing/redacted');continue
        if item.get('itemType') not in (2,3,16):
            add('invalid',key,'Definition is not equippable weapon, armor or subclass (recipe hashes are not item versions)');continue
        if item.get('classType') not in (cls,3):add('invalid',key,'Wrong class')
        equip=item.get('equippingBlock')
        if not equip:
            add('unknown',key,'No equipping block');continue
        bucket=equip.get('equipmentSlotTypeHash')
        if not bucket:add('unknown',key,'Missing equipment slot')
        elif bucket in buckets:add('invalid',key,'Two equipped items occupy same slot',other=buckets[bucket])
        else:buckets[bucket]=key
        label=equip.get('uniqueLabelHash') or equip.get('uniqueLabel')
        if label:
            if label in labels:add('invalid',key,'Duplicate equipping unique label (e.g. exotic limit)',other=labels[label])
            else:labels[label]=key
        instance=selection.get('owned_instance')
        if instance:
            identity=instance.get('item_instance_id')
            if not identity or identity in instances:raise ValueError('Owned instance ids must be nonempty and unique')
            instances.add(identity)
            if str(instance.get('item_hash'))!=key:raise ValueError('Owned instance hash mismatch')
            if not instance.get('provenance') or not instance.get('retrieved_at'):
                raise ValueError('Owned socket evidence needs provenance and retrieval time')
        elif purpose=='owned_equipment':add('unknown',key,'No owned-instance evidence')
        sockets=item.get('sockets',{}).get('socketEntries',[])
        selected=set()
        for plug in selection.get('plugs',[]):
            n=integer(plug['socket'],'socket index',0,max(0,len(sockets)-1))
            if n>=len(sockets):raise ValueError('Socket index out of range')
            if n in selected:raise ValueError('Only one active plug per socket')
            selected.add(n);ph=str(plug['plug_hash']);entry=sockets[n]
            path=plug.get('path','random_roll')
            members={};source=''
            if path=='random_roll':
                set_hash=entry.get('randomizedPlugSetHash')
                definition=manifest.get('DestinyPlugSetDefinition',set_hash) if set_hash else None
                if definition:
                    members={str(v['plugItemHash']):v for v in definition.get('reusablePlugItems',[])};source='randomizedPlugSetHash'
            elif path=='reusable':
                members={str(v['plugItemHash']):v for v in entry.get('reusablePlugItems',[])}
                set_hash=entry.get('reusablePlugSetHash')
                definition=manifest.get('DestinyPlugSetDefinition',set_hash) if set_hash else None
                if definition:members.update({str(v['plugItemHash']):v for v in definition.get('reusablePlugItems',[])})
                source='reusable plugs; insertion requirements not established'
            elif path=='initial':
                members={str(entry.get('singleInitialItemHash')):{}};source='initial plug only'
            elif path=='crafting':
                recipe_hash=item.get('inventory',{}).get('recipeItemHash')
                recipe=manifest.get('DestinyInventoryItemDefinition',recipe_hash) if recipe_hash else None
                rs=recipe.get('sockets',{}).get('socketEntries',[]) if recipe else []
                if n<len(rs):
                    definition=manifest.get('DestinyPlugSetDefinition',rs[n].get('reusablePlugSetHash'))
                    if definition:members={str(v['plugItemHash']):v for v in definition.get('reusablePlugItems',[])}
                source='recipe socket; level/material/unlock requirements not established'
            elif path!='owned':raise ValueError('Unknown plug evidence path')
            owned=None
            if instance:
                owned=instance.get('sockets',{}).get(str(n))
                if owned and str(owned.get('plug_hash'))==ph and owned.get('is_enabled') is True:
                    add('supported',key,f'Socket {n}: selected active plug observed on supplied owned instance',plug_hash=ph)
                else:owned=None
            if path=='owned':
                if not owned:add('unknown',key,f'Socket {n}: active owned plug not established')
                continue
            if not members:
                add('unknown',key,f'Socket {n}: no complete pool for selected path',path=path);continue
            if ph not in members:
                add('invalid' if purpose=='theoretical_roll' else 'unknown',key,
                    f'Socket {n}: plug absent from selected snapshot pool',plug_hash=ph,path=path)
                continue
            can_roll=members[ph].get('currentlyCanRoll')
            if path=='random_roll' and can_roll is False:
                add('invalid' if purpose=='theoretical_roll' else 'unknown',key,f'Socket {n}: currentlyCanRoll=false; does not invalidate historical ownership')
            else:add('supported',key,f'Socket {n}: pool membership supported',plug_hash=ph,path=path,pool=source)
            if path in ('crafting','reusable'):
                add('unknown',key,f'Socket {n}: dynamic insertion/enhancement/crafting requirements need instance evidence')
            if purpose=='owned_equipment' and not owned:
                add('unknown',key,f'Socket {n}: membership does not prove this owned item has the plug active')
        if not selection.get('plugs'):add('unknown',key,'Perk/socket selections not checked')
    for required in document.get('required_buckets',[]):
        if int(required) not in buckets:add('invalid','completeness','Missing required slot',bucket=required)
    if not document.get('required_buckets'):add('unknown','completeness','Full loadout completeness not specified')
    if rules is not None:
        if rules.get('sandbox')!=document.get('sandbox') or rules.get('class_type')!=cls or not rules.get('provenance'):
            add('unknown','rules','Rule pack patch/class/provenance mismatch')
        else:
            subclass=document.get('subclass',{});sid=subclass.get('id')
            aspect_defs=unique(rules.get('aspects',[]),'aspects')
            aspect_ids=subclass.get('aspects',[]);fragment_ids=subclass.get('fragments',[])
            if len(aspect_ids)!=len(set(aspect_ids)) or len(fragment_ids)!=len(set(fragment_ids)):
                add('invalid','subclass','Duplicate aspects/fragments')
            max_aspects=integer(rules['max_aspects'],'max_aspects',0,10)
            if len(aspect_ids)>max_aspects:add('invalid','subclass','Too many aspects')
            slots=0;complete=True
            for aid in aspect_ids:
                aspect=aspect_defs.get(aid)
                if not aspect or sid not in aspect.get('subclasses',[]):
                    add('unknown','subclass','Aspect not established for subclass',aspect=aid);complete=False
                else:slots+=integer(aspect['fragment_slots'],'fragment slots',0,10)
            allowed=rules.get('fragments',{}).get(sid)
            if allowed is None:add('unknown','subclass','No complete fragment pool')
            elif any(f not in allowed for f in fragment_ids):add('invalid','subclass','Fragment outside supplied complete pool')
            if complete and len(fragment_ids)>slots:add('invalid','subclass','Fragment capacity exceeded')
            artifact=document.get('artifact',{})
            if artifact:
                rule=rules.get('artifact',{})
                mods=artifact.get('mods',[])
                if artifact.get('id')!=rule.get('id'):add('invalid','artifact','Artifact era/id mismatch')
                if len(mods)!=len(set(mods)):add('invalid','artifact','Duplicate artifact mods')
                allowed_mods=rule.get('mods',{})
                if not all(m in allowed_mods for m in mods):add('unknown','artifact','Unknown artifact mods')
                else:
                    cost=sum(integer(allowed_mods[m]['cost'],'artifact cost',0,100) for m in mods)
                    if cost>integer(rule['budget'],'artifact budget',0,100):add('invalid','artifact','Artifact budget exceeded')
                    selected_mods=set(mods)
                    for m in mods:
                        for required in allowed_mods[m].get('requires',[]):
                            if required not in selected_mods:add('invalid','artifact','Missing artifact prerequisite',mod=m,required=required)
                        if selected_mods & set(allowed_mods[m].get('excludes',[])):add('invalid','artifact','Mutually exclusive artifact mods',mod=m)
            for piece in document.get('armor_mods',[]):
                armor_rules=rules.get('armor',{});slot=piece.get('slot')
                slot_rules=armor_rules.get('slots',{}).get(slot)
                limit=integer(slot_rules['energy_capacity'] if slot_rules else piece['energy_capacity'],'mod capacity',0,100)
                if slot_rules and len(piece['mods'])>integer(slot_rules['socket_count'],'mod socket count',0,100):add('invalid','armor_mods','Armor mod socket count exceeded',slot=slot)
                total=0;counts={}
                for mod in piece['mods']:
                    definition=armor_rules.get('mods',{}).get(mod.get('id'))
                    if definition:
                        cost=integer(definition['energy_cost'],'audited mod cost',0,100)
                        if slot not in definition['allowed_slots']:add('invalid','armor_mods','Mod not permitted in armor slot',mod=mod['id'],slot=slot)
                        counts[mod['id']]=counts.get(mod['id'],0)+1
                        if counts[mod['id']]>definition.get('max_copies',100):add('invalid','armor_mods','Mod duplicate cap exceeded',mod=mod['id'])
                        if 'energy_cost' in mod and mod['energy_cost']!=cost:add('invalid','armor_mods','Caller mod cost differs from audited rule',mod=mod['id'])
                    else:
                        add('unknown','armor_mods','No audited definition for mod cost/slot/copy constraints',mod=mod.get('id'))
                        cost=integer(mod['energy_cost'],'declared mod cost',0,100)
                    total+=cost
                if total>limit:add('invalid','armor_mods','Energy budget exceeded',slot=piece.get('slot'))
            add('supported','rules','Checks applied to caller-supplied audited rule pack; correctness depends on its evidence')
    else:add('unknown','subclass/artifact/mods','No audited rule pack; these constraints not checked')
    add('unknown','server','Ownership, disabled items, activity restrictions and all cross-socket conditions need live evidence')
    invalid=any(x['status']=='invalid' for x in checks)
    return dict(status='invalid' if invalid else 'structurally_compatible_runtime_unverified',checks=checks,
        manifest=manifest.metadata,purpose=purpose,
        limitation='A finite manifest/policy check is not a complete legal-loadout solver or server equipability certification.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('loadout');p.add_argument('--db',required=True);p.add_argument('--rules');p.add_argument('--out')
    a=p.parse_args()
    def run():
        with closing(Manifest(a.db)) as m:return validate(load(a.loadout),m,load(a.rules) if a.rules else None)
    cli_error(p,lambda:emit(run(),a.out))


if __name__=='__main__':main()
