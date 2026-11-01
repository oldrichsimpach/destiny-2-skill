"""Typed incoming damage, timed DR, separate overshield pools and healing events."""
import argparse
import math
from engine_common import load, emit, finite, unique, cli_error
from evidence import Resolver


class Survivor:
    def __init__(self,model,resolver):
        self.model=model;self.resolver=resolver;self.unit=model.get('health_unit','hp')
        self.maximum=resolver.value(model['max_hp'],self.unit,'max HP',low=1e-9)
        self.hp=resolver.value(model.get('initial_hp',model['max_hp']),self.unit,'initial HP',high=self.maximum)
        self.death_time=0 if self.hp==0 else None
        self.logs=[];self.pools=[];self.dr=[];self.last_time=0
        for x in unique(model.get('overshields',[]),'overshields').values():
            cap=resolver.value(x['capacity'],self.unit,'overshield capacity')
            self.pools.append(dict(id=x['id'],capacity=cap,
                amount=resolver.value(x.get('initial',x['capacity']),self.unit,'initial overshield',high=cap),
                start=finite(x.get('start',0),'shield start'),end=finite(x['end'],'shield end'),
                types=x.get('damage_types',[]),dr=resolver.value(x.get('dr',0),'fraction','shield DR',component='incoming',high=1)))
            if self.pools[-1]['end']<=self.pools[-1]['start']:raise ValueError('Overshield interval must be positive')
        for x in unique(model.get('resistances',[]),'resistances').values():
            if not x.get('independence_group'):raise ValueError('DR requires an explicit independence_group')
            if not x.get('damage_types'):raise ValueError('DR needs explicit affected damage types')
            self.dr.append(dict(x,fraction=resolver.value(x['fraction'],'fraction','DR '+x['id'],component='incoming',high=1)))
            if finite(x['end'],'DR end')<=finite(x.get('start',0),'DR start'):raise ValueError('Invalid DR interval')

    def factor(self,event,t):
        groups={};tags=set(event.get('tags',[]))
        for x in self.dr:
            if not x.get('start',0)<=t<x['end']:continue
            if event['damage_type'] not in x['damage_types']:continue
            if not set(x.get('requires_tags',[]))<=tags:continue
            group=x['independence_group']
            groups[group]=max(groups.get(group,0),x['fraction'])
        return math.prod(1-v for v in groups.values()),groups

    def process(self,event):
        t=finite(event['time'],'survival event time')
        if t<self.last_time:raise ValueError('Survival events must be time-ordered')
        self.last_time=t
        if self.death_time is not None:
            self.logs.append(dict(time=t,kind=event['kind'],ignored='already dead'));return
        kind=event['kind']
        amount=self.resolver.value(event['amount'],self.unit,'survival '+kind)
        if kind=='heal':
            used=min(amount,self.maximum-self.hp);self.hp+=used
            self.logs.append(dict(time=t,kind=kind,used=used,wasted=amount-used,hp=self.hp));return
        if kind=='shield_grant':
            pools=[p for p in self.pools if p['id']==event['shield_id'] and p['start']<=t<p['end']]
            if not pools:raise ValueError('Shield grant needs a defined active pool')
            pool=pools[0];used=min(amount,pool['capacity']-pool['amount']);pool['amount']+=used
            self.logs.append(dict(time=t,kind=kind,used=used,wasted=amount-used,shield_id=pool['id']));return
        if kind!='incoming':raise ValueError('Unsupported survival event')
        if not event.get('damage_type'):raise ValueError('Incoming damage needs a damage_type')
        factor,groups=self.factor(event,t);remaining=amount*factor;absorbed={}
        for pool in self.pools:
            if not pool['start']<=t<pool['end'] or pool['amount']<=0:continue
            if pool['types'] and event['damage_type'] not in pool['types']:continue
            sf=1-pool['dr']
            if sf==0:
                absorbed[pool['id']]=remaining;remaining=0;break
            applied=min(pool['amount'],remaining*sf)
            pool['amount']-=applied;raw_consumed=applied/sf
            remaining=max(0,remaining-raw_consumed);absorbed[pool['id']]=applied
        hp_damage=min(self.hp,remaining);overkill=max(0,remaining-self.hp);self.hp-=hp_damage
        if self.hp<=0:self.hp=0;self.death_time=t
        self.logs.append(dict(time=t,kind=kind,raw=amount,remaining_factor=factor,dr_groups=groups,
            shield_damage=absorbed,hp_damage=hp_damage,overkill=overkill,hp=self.hp))

    def report(self,duration):
        return dict(alive=self.death_time is None,death_time=self.death_time,
            time_alive=duration if self.death_time is None else min(duration,self.death_time),
            hp=self.hp,health_unit=self.unit,
            overshields=[dict(id=p['id'],amount=p['amount'] if p['start']<=duration<p['end'] else 0) for p in self.pools],
            events=self.logs,limitation='Only declared attack types, independent DR groups, pools and healing events. No inferred enemy attack rates, AI, recovery or damage gates.')


def evaluate(document,ledger=None):
    duration=finite(document['duration'],'duration',1e-9,3600)
    resolver=Resolver(document,ledger);state=Survivor(document['survival'],resolver)
    events=document['survival'].get('events',[])
    if len(events)>100000:raise ValueError('Too many survival events')
    for _,event in sorted(enumerate(events),key=lambda p:(p[1]['time'],p[0])):
        finite(event['time'],'event time')
        if event['time']<duration:state.process(event)
    return dict(**state.report(duration),**resolver.report(),boundary='[0,T); equal-time events retain input order; healing never revives')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('scenario');p.add_argument('--ledger');p.add_argument('--out')
    a=p.parse_args();cli_error(p,lambda:emit(evaluate(load(a.scenario),load(a.ledger) if a.ledger else None),a.out))


if __name__=='__main__':main()
