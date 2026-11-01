"""Bounded event/state model: ammo, actions, timed procs, abilities and incoming damage."""
import argparse
import copy
import heapq
import math
import random
from engine_common import load, emit, finite, integer, unique, cli_error
from evidence import Resolver
from survivability import Survivor

COMPONENTS={'weapon_impact','weapon_explosion','weapon_combined','dot','ability','super'}


class Simulation:
    def __init__(self,scenario,build,profile=None,ledger=None):
        self.s=scenario;self.build=build;self.profile=profile or {'id':'declared'}
        self.rng=random.Random(scenario.get('seed',0)+scenario.get('_trial',0)) if scenario.get('stochastic_trials') else None
        self.accuracy_draws={}
        self.duration=finite(scenario['duration'],'duration',1e-9,3600)
        self.resolver=Resolver(scenario,ledger);self.unit=scenario['damage_unit']
        self.now=0.;self.cursor=finite(build.get('setup_seconds',0),'setup',0,3600)+finite(self.profile.get('extra_setup_seconds',0),'extra setup',0,3600)
        self.q=[];self.sequence=0;self.events=[];self.fires=[];self.activations=[];self.energy_log=[];self.refill_log=[]
        self.weapons=copy.deepcopy(unique(build.get('weapons',[]),'weapons'))
        self.abilities=copy.deepcopy(unique(build.get('abilities',[]),'abilities'))
        self.effects=copy.deepcopy(unique(build.get('effects',[]),'effects'))
        self.active={};self.counters={};self.icd={};self.skipped_procs=[]
        self.equipped=build.get('initial_weapon')
        if self.equipped is not None and self.equipped not in self.weapons:raise ValueError('Unknown initial weapon')
        self.blocked=self.intervals(self.profile.get('movement_windows',[]),'movement')
        self.vulnerable=self.intervals(scenario.get('target',{}).get('vulnerability_windows',[[0,self.duration]]),'vulnerability')
        self.survivor=Survivor(build['survival'],self.resolver) if 'survival' in build else None
        if self.survivor:
            incoming=build['survival'].get('events',[])
            if len(incoming)>100000:raise ValueError('Too many incoming events')
            for ev in incoming:self.enqueue(finite(ev['time'],'incoming time'),0,'survival',ev)
        for k,w in self.weapons.items():
            w['ammo_left']=integer(w['ammo'],'total ammo')
            w['magazine']=integer(w['magazine'],'magazine',1,100000)
            w['loaded']=min(w['ammo_left'],w['magazine'])
            w['ammo_capacity']=integer(w.get('ammo_capacity',w['ammo']),'ammo capacity',w['ammo'],100000)
            w['ammo_spent']=0;w['ammo_gained']=0;w['refill_generation']=0
            for field in ['charge_seconds','recovery_seconds','reload_seconds','ready_seconds','stow_seconds']:
                w[field]=self.value(w.get(field,0),'seconds',k+'.'+field)
            if w['charge_seconds']+w['recovery_seconds']<=0:raise ValueError('Weapon cycle must have positive duration')
            w['ammo_cost']=integer(w.get('ammo_cost',1),'ammo cost',1,w['magazine'])
            self.prepare_components(w['components'],k)
            if 'refill' in w:
                rule=w['refill']
                if rule['scope'] not in ('stowed','not_firing'):raise ValueError('Unknown passive refill scope')
                rule['delay_seconds']=self.value(rule['delay_seconds'],'seconds',k+'.refill delay',low=1e-9)
                if rule.get('repeat_seconds') is not None:rule['repeat_seconds']=self.value(rule['repeat_seconds'],'seconds',k+'.refill interval',low=1e-9)
                integer(rule['rounds_per_tick'],'refill rounds',1,100000)
                integer(rule['capacity_rounds'],'refill capacity',w['magazine'],100000)
                if rule['scope']=='not_firing' or self.equipped!=k:self.schedule_refill(k,0)
        for k,a in self.abilities.items():
            a['cooldown_seconds']=self.value(a['cooldown_seconds'],'seconds',k+'.cooldown',low=1e-9)
            a['cast_seconds']=self.value(a['cast_seconds'],'seconds',k+'.cast',low=1e-9)
            a['max_charges']=integer(a.get('max_charges',1),'ability charges',1,10)
            a['energy']=self.value(a.get('initial_energy',a['max_charges']),'charges',k+'.initial_energy',high=a['max_charges'])
            a['initial_energy_resolved']=a['energy'];a['passive_gained']=0.;a['granted']=0.;a['spent']=0.;a['wasted']=0.
            self.prepare_components(a.get('components',[]),k)
        category_rules={}
        for k,e in self.effects.items():
            e['kind']=e.get('kind','damage')
            if e['kind'] not in ('damage','recharge','instant'):raise ValueError('Unknown effect kind')
            e['duration_seconds']=self.value(e.get('duration_seconds',0),'seconds',k+'.duration')
            e['icd_seconds']=self.value(e.get('icd_seconds',0),'seconds',k+'.ICD')
            e['activation_delay']=self.value(e.get('activation_delay',0),'seconds',k+'.delay')
            if e['kind']!='instant':
                if not e.get('category') or e.get('stacking') not in ('max','product','sum_bonus'):
                    raise ValueError('Effect needs explicit category and stacking rule')
                prior=category_rules.setdefault((e['kind'],e['category']),e['stacking'])
                if prior!=e['stacking']:raise ValueError('Inconsistent stacking rules in same category')
                factor_spec=e['factor']
                if isinstance(factor_spec,dict) and 'claim' in factor_spec:
                    record=self.resolver.ledger.records[factor_spec['claim']]
                    scopes=e.get('components',[]) if e['kind']=='damage' else ['ability_recharge']
                    if not set(scopes)<=set(record.get('components',[])):raise ValueError('Effect claim used outside its component/role scope')
                    if record.get('stacking_group') and (e['category']!=record['stacking_group'] or e['stacking']!='max'):
                        raise ValueError('Source-defined stacking category cannot be relabeled')
                e['factor']=self.value(factor_spec,'factor',k+'.factor')
                if e['stacking']=='sum_bonus' and e['factor']<1:raise ValueError('sum_bonus needs factors >=1')
                if e['duration_seconds']<=0:raise ValueError('Timed effect requires positive duration')
            if e['kind']=='damage' and (not e.get('components') or not set(e['components'])<=COMPONENTS):
                raise ValueError('Damage effects need explicit component scope')
            if e['kind']=='recharge' and not e.get('ability_ids'):raise ValueError('Recharge effect needs ability ids')
            trigger=e.get('trigger')
            if trigger:
                if trigger['on'] not in ('fire','hit','crit','cast','kill','pickup'):raise ValueError('Unsupported trigger event')
                integer(trigger.get('count',1),'trigger count',1,100000)
                finite(trigger.get('within_seconds',self.duration),'trigger window',0,3600)
        self.target_scalar=self.value(scenario.get('target',{}).get('damage_scalar',1),'factor','target damage scalar',component='target_scaling')

    def value(self,spec,unit,label,component=None,low=0,high=None):
        return self.resolver.value(spec,unit,label,component,low,high)

    @staticmethod
    def intervals(rows,label):
        out=[]
        for x in rows:
            start=finite(x[0],label+' start');end=finite(x[1],label+' end')
            if end<=start:raise ValueError(label+' interval must be positive')
            out.append((start,end))
        return sorted(out)

    def prepare_components(self,components,owner):
        unique(components,owner+' components')
        for c in components:
            if c['kind'] not in COMPONENTS:raise ValueError('Unsupported component kind')
            c['body']=self.value(c['body'],self.unit,owner+'.'+c['id']+'.body',c['kind'])
            c['crit']=self.value(c['crit'],self.unit,owner+'.'+c['id']+'.crit',c['kind']) if 'crit' in c else c['body']
            c['hit_probability']=finite(c.get('hit_probability',1),'hit probability',0,1)*finite(self.profile.get('hit_scale',1),'hit scale',0,1)
            c['crit_given_hit']=finite(c.get('crit_given_hit',0),'crit probability',0,1)*finite(self.profile.get('crit_scale',1),'crit scale',0,1)
            c['offsets']=[finite(x,'damage offset',0,3600) for x in c.get('offsets',[0])]
            if len(c['offsets'])>10000:raise ValueError('Too many ticks')
            if c.get('snapshot','hit') not in ('hit','fire'):raise ValueError('Snapshot rule must be hit or fire')
            c['range_factor']=1
            if 'falloff_points' in c:
                distance=self.profile.get('distance_m',self.s.get('target',{}).get('distance_m'))
                distance=self.value(distance,'meters','target distance')
                points=[(self.value(p[0],'meters','falloff distance'),self.value(p[1],'factor','falloff factor',high=1)) for p in c['falloff_points']]
                if len(points)<2 or any(a[0]>=b[0] or a[1]<b[1] for a,b in zip(points,points[1:])):raise ValueError('Falloff points must increase in distance and not increase in damage')
                if not points[0][0]<=distance<=points[-1][0]:raise ValueError('Distance outside measured falloff range')
                exact=[f for d,f in points if distance==d]
                if exact:c['range_factor']=exact[0]
                elif c.get('falloff_interpolation')=='linear':
                    for (x,y),(xx,yy) in zip(points,points[1:]):
                        if x<distance<xx:c['range_factor']=y+(yy-y)*(distance-x)/(xx-x);break
                else:raise ValueError('Interpolation between falloff samples not explicitly authorized')

    def enqueue(self,t,priority,kind,data):
        finite(t,'event time')
        self.sequence+=1
        if self.sequence>200000:raise ValueError('Event budget exceeded')
        heapq.heappush(self.q,(t,priority,self.sequence,kind,data))

    def factor(self,kind,t,component=None,owner=None,element=None):
        groups={}
        for key,end in self.active.items():
            e=self.effects[key]
            if e['kind']!=kind or not t<end:continue
            if kind=='damage':
                if component not in e['components']:continue
                if e.get('weapon_ids') and owner not in e['weapon_ids']:continue
                if e.get('element') and element!=e['element']:continue
            elif owner not in e['ability_ids']:continue
            groups.setdefault((e['category'],e['stacking']),[]).append(e['factor'])
        factors=[]
        for (_,rule),values in groups.items():
            factors.append(max(values) if rule=='max' else math.prod(values) if rule=='product' else 1+sum(v-1 for v in values))
        return math.prod(factors)

    def regen(self,to):
        if to<self.now:raise ValueError('Time moved backwards')
        bounds=sorted({self.now,to}|{end for end in self.active.values() if self.now<end<to})
        for start,end in zip(bounds,bounds[1:]):
            for key,a in self.abilities.items():
                potential=(end-start)/a['cooldown_seconds']*self.factor('recharge',start,owner=key)
                gain=min(a['max_charges']-a['energy'],potential)
                a['energy']+=gain;a['passive_gained']+=gain
        self.now=to

    def advance(self,to):
        finite(to,'advance time')
        to=min(to,self.duration)
        while self.q and self.q[0][0]<=to and self.q[0][0]<self.duration:
            t,_,_,kind,data=heapq.heappop(self.q);self.regen(t)
            if kind=='activate':self.activate(data,t)
            elif kind=='survival':self.survivor.process(data)
            elif kind=='damage':self.damage(data,t)
            elif kind=='signal':self.trigger(data['event'],data.get('source'),t,True,data.get('element'))
            elif kind=='refill':self.refill(data,t)
        self.regen(to)

    def schedule_refill(self,key,t):
        w=self.weapons[key];w['refill_generation']+=1
        self.enqueue(t+w['refill']['delay_seconds'],15,'refill',dict(weapon=key,generation=w['refill_generation']))

    def refill(self,data,t):
        w=self.weapons[data['weapon']];rule=w['refill']
        if data['generation']!=w['refill_generation'] or (rule['scope']=='stowed' and self.equipped==data['weapon']):return
        before=w['loaded'];w['loaded']=min(w['ammo_left'],rule['capacity_rounds'],before+rule['rounds_per_tick'])
        self.refill_log.append(dict(time=t,weapon=data['weapon'],rounds_loaded=w['loaded']-before,total_left=w['ammo_left']))
        if rule.get('repeat_seconds') is not None:self.enqueue(t+rule['repeat_seconds'],15,'refill',data)

    def activate(self,key,t):
        e=self.effects[key]
        if self.profile.get('effect_availability',{}).get(key,True) is not True:return
        if not set(e.get('requires_conditions',[]))<=set(self.s.get('satisfied_conditions',[])):
            self.skipped_procs.append(dict(time=t,effect=key,reason='conditions not established'));return
        if t<self.icd.get(key,0):return
        if t<self.active.get(key,0) and not e.get('refreshable',True):return
        self.active[key]=t+e['duration_seconds'];self.icd[key]=t+e['icd_seconds']
        self.activations.append(dict(time=t,effect=key,end=self.active[key]))
        for grant in e.get('energy_grants',[]):
            if grant['ability'] not in self.abilities:raise ValueError('Unknown energy grant ability')
            a=self.abilities[grant['ability']]
            nominal=self.value(grant['amount'],'charges',key+'.grant',component='ability_energy')
            ces=self.value(grant.get('chunk_scalar',1),'factor',key+'.chunk scalar',component='ability_energy')
            cms=self.value(grant.get('class_mod_scalar',1),'factor',key+'.class mod scalar',component='ability_energy')
            raw=nominal*ces*cms;gain=min(raw,a['max_charges']-a['energy'])
            a['energy']+=gain;a['granted']+=gain;a['wasted']+=raw-gain
            self.energy_log.append(dict(time=t,effect=key,ability=grant['ability'],nominal=nominal,chunk_scalar=ces,
                class_mod_scalar=cms,actual=gain,wasted=raw-gain,energy=a['energy']))
        for heal in e.get('heals',[]):
            if not self.survivor:raise ValueError('Healing proc requires survival model')
            self.enqueue(t,35,'survival',dict(time=t,kind='heal',amount=heal['amount']))

    def trigger(self,event,owner,t,guaranteed,element=None):
        for key,e in self.effects.items():
            tr=e.get('trigger')
            if not tr or tr['on']!=event:continue
            if tr.get('source_ids') and owner not in tr['source_ids']:continue
            if tr.get('element') and element!=tr['element']:continue
            if not guaranteed:
                self.skipped_procs.append(dict(time=t,effect=key,reason='probabilistic event cannot establish deterministic trigger'));continue
            if t<self.icd.get(key,0) or (t<self.active.get(key,0) and not e.get('refreshable',True)):continue
            counter=[x for x in self.counters.get(key,[]) if t-x[0]<=tr.get('within_seconds',self.duration)]
            counter.append((t,owner));self.counters[key]=counter
            required=tr.get('distinct_sources')
            ready=(set(required)<={x[1] for x in counter}) if required else len(counter)>=tr.get('count',1)
            if ready:
                self.counters[key]=[]
                self.enqueue(t+e['activation_delay'],30,'activate',key)

    def damage(self,data,t):
        c=data['component'];vulnerable=any(a<=t<b for a,b in self.vulnerable)
        f=data.get('snapshot_factor')
        if f is None:f=self.factor('damage',t,c['kind'],data['owner'],c.get('element'))
        ph,pc=c['hit_probability'],c['crit_given_hit']
        if self.rng:
            key=(data['owner'],data['fire_time'],c.get('accuracy_group',c['id']))
            if key not in self.accuracy_draws:self.accuracy_draws[key]=(self.rng.random(),self.rng.random())
            hit_draw,crit_draw=self.accuracy_draws[key]
            ph=int(hit_draw<ph);pc=int(crit_draw<pc)
        expected=ph*(pc*c['crit']+(1-pc)*c['body'])
        damage=expected*f*self.target_scalar*c['range_factor'] if vulnerable else 0
        finite(damage,'calculated damage')
        self.events.append(dict(time=t,fire_time=data['fire_time'],owner=data['owner'],component=c['id'],kind=c['kind'],
            expected_damage=damage,effect_factor=f,range_factor=c['range_factor'],immune=not vulnerable,
            deterministic=ph in (0,1) and pc in (0,1)))
        if vulnerable and c.get('counts_for_triggers',False):
            if ph>0:self.trigger('hit',data['owner'],t,ph==1,c.get('element'))
            if ph>0 and pc>0:self.trigger('crit',data['owner'],t,ph==1 and pc==1,c.get('element'))

    def schedule_damage(self,owner,components,fire_time):
        for c in components:
            for offset in c['offsets']:
                packet=dict(owner=owner,component=c,fire_time=fire_time)
                if c.get('snapshot','hit')=='fire':packet['snapshot_factor']=self.factor('damage',fire_time,c['kind'],owner,c.get('element'))
                self.enqueue(fire_time+offset,20,'damage',packet)

    def alive(self):return not self.survivor or self.survivor.death_time is None

    def action_time(self):
        t=self.cursor
        # Overlapping movement intervals form a union.
        for start,end in self.blocked:
            if start<=t<end:t=end
        self.cursor=t;self.advance(t)
        return t<self.duration and self.alive()

    def ready_ability(self,key,auto_wait):
        a=self.abilities[key]
        while a['energy']<1-1e-10 and self.cursor<self.duration and self.alive():
            if not auto_wait:raise ValueError('Ability lacks energy: '+key)
            rate=self.factor('recharge',self.now,owner=key)/a['cooldown_seconds']
            ready=self.now+(1-a['energy'])/rate if rate>0 else math.inf
            changes=[x for x in self.active.values() if x>self.now]+([self.q[0][0]] if self.q else [])+[self.duration]
            to=min([ready]+changes)
            if not math.isfinite(to) or to<=self.now:raise ValueError('Ability cannot become ready')
            self.cursor=to;self.advance(to)
        return a['energy']>=1-1e-10 and self.alive() and self.cursor<self.duration

    def run(self):
        actions=self.build.get('actions',[])
        if len(actions)>10000:raise ValueError('Too many actions')
        for action in actions:
            if self.cursor>=self.duration or not self.alive():break
            if 'at' in action:
                t=finite(action['at'],'action at')
                if t<self.cursor-1e-9:raise ValueError('Action at precedes animation/cadence lock')
                self.cursor=t
            if not self.action_time():break
            kind=action['type']
            if kind=='wait':
                self.cursor+=self.value(action['seconds'],'seconds','wait');self.advance(self.cursor)
            elif kind=='activate':
                if action['effect'] not in self.effects:raise ValueError('Unknown effect')
                self.enqueue(self.cursor,10,'activate',action['effect']);self.advance(self.cursor)
            elif kind=='signal':
                if action['event'] not in ('kill','pickup'):raise ValueError('Only external kill/pickup signals allowed')
                if not action.get('provenance'):raise ValueError('External signal needs explicit evidence/assumption')
                self.resolver.assumptions.append(dict(field='external '+action['event'],value=self.cursor,provenance=action['provenance']))
                self.enqueue(self.cursor,10,'signal',action);self.advance(self.cursor)
            elif kind=='ammo_pickup':
                key=action['weapon'];w=self.weapons[key]
                amount=integer(action['rounds'],'pickup rounds',1,100000)
                gain=min(amount,w['ammo_capacity']-w['ammo_left']);w['ammo_left']+=gain;w['ammo_gained']+=gain
                self.refill_log.append(dict(time=self.cursor,weapon=key,pickup=True,gained=gain,wasted=amount-gain))
                self.trigger('pickup',key,self.cursor,True);self.advance(self.cursor)
            elif kind in ('equip','reload','fire'):
                key=action['weapon']
                if key not in self.weapons:raise ValueError('Unknown weapon')
                w=self.weapons[key]
                if self.equipped!=key:
                    prior=self.equipped
                    self.cursor+=(self.weapons[prior]['stow_seconds'] if prior else 0)
                    self.advance(self.cursor);self.equipped=key
                    if prior and self.weapons[prior].get('refill',{}).get('scope')=='stowed':self.schedule_refill(prior,self.cursor)
                    if w.get('refill',{}).get('scope')=='stowed':w['refill_generation']+=1
                    self.cursor+=w['ready_seconds'];self.advance(self.cursor)
                if kind=='equip':continue
                if kind=='reload':
                    self.cursor+=w['reload_seconds'];self.advance(self.cursor)
                    if self.cursor<self.duration and self.alive():w['loaded']=min(w['magazine'],w['ammo_left'])
                    continue
                count=integer(action.get('count',1),'fire count',1,100000)
                for _ in range(count):
                    if not self.action_time():break
                    if w['ammo_left']<w['ammo_cost']:break
                    if w['loaded']<w['ammo_cost']:
                        if not action.get('auto_reload',False):raise ValueError('Magazine empty; explicit reload or auto_reload required')
                        self.cursor+=w['reload_seconds'];self.advance(self.cursor)
                        if self.cursor>=self.duration or not self.alive():break
                        w['loaded']=min(w['magazine'],w['ammo_left'])
                        if w['loaded']<w['ammo_cost']:break
                    self.cursor+=w['charge_seconds'];self.advance(self.cursor)
                    if self.cursor>=self.duration or not self.alive():break
                    w['loaded']-=w['ammo_cost'];w['ammo_left']-=w['ammo_cost']
                    w['ammo_spent']+=w['ammo_cost']
                    if w.get('refill',{}).get('scope')=='not_firing':self.schedule_refill(key,self.cursor)
                    self.fires.append(dict(time=self.cursor,weapon=key,ammo_cost=w['ammo_cost']))
                    self.trigger('fire',key,self.cursor,True);self.advance(self.cursor)
                    self.schedule_damage(key,w['components'],self.cursor)
                    self.advance(self.cursor)
                    self.cursor+=w['recovery_seconds'];self.advance(self.cursor)
            elif kind=='cast':
                key=action['ability']
                if key not in self.abilities:raise ValueError('Unknown ability')
                if not self.ready_ability(key,action.get('auto_wait',False)):continue
                if not self.action_time():break
                a=self.abilities[key]
                # Movement can delay readiness; it never spends energy before this check.
                a['energy']=max(0,a['energy']-1);a['spent']+=1
                self.energy_log.append(dict(time=self.cursor,ability=key,cast=True,energy=a['energy']))
                self.trigger('cast',key,self.cursor,True);self.advance(self.cursor)
                self.schedule_damage(key,a.get('components',[]),self.cursor+a['cast_seconds'])
                self.cursor+=a['cast_seconds'];self.advance(self.cursor)
            else:raise ValueError('Unknown action type: '+kind)
        self.advance(self.duration)
        self.events.sort(key=lambda x:x['time'])
        windows=sorted(set(self.s.get('windows_seconds',[self.duration])))
        rows=[]
        for t in windows:
            finite(t,'window',1e-9,self.duration)
            d=math.fsum(e['expected_damage'] for e in self.events if e['time']<t)
            rows.append(dict(seconds=t,expected_damage=d,dps=d/t))
        abilities={k:dict(final_energy=a['energy'],initial_energy=a['initial_energy_resolved'],passive_gained=a['passive_gained'],
            grants_gained=a['granted'],spent=a['spent'],wasted_grants=a['wasted']) for k,a in self.abilities.items()}
        hp=self.s.get('target',{}).get('hp')
        crossing=None
        if hp is not None:
            hp=self.value(hp,self.unit,'target HP',low=1e-9);cumulative=0
            for e in self.events:
                cumulative+=e['expected_damage']
                if cumulative>=hp:crossing=e['time'];break
        if self.skipped_procs:self.resolver.conditional.append('Nonlinear proc probabilities unresolved in expectation mode; use stochastic_trials or deterministic observations')
        return dict(name=self.build['name'],profile=self.profile.get('id','declared'),windows=rows,events=self.events,
            ammo={k:dict(total_left=w['ammo_left'],loaded=w['loaded'],spent=w['ammo_spent'],picked_up=w['ammo_gained']) for k,w in self.weapons.items()},
            refill_events=self.refill_log,
            fire_events=self.fires,ability_resources=abilities,energy_events=self.energy_log,effect_activations=self.activations,
            skipped_procs=self.skipped_procs,planned_utility=self.build.get('utility',[]),
            target_hp_crossing=crossing,ttk_kind='deterministic event model' if all(e['deterministic'] for e in self.events) else 'expected damage crossing; not stochastic TTK',
            survival=self.survivor.report(self.duration) if self.survivor else None,**self.resolver.report())


def lead_changes(rows):
    changes=[]
    for i,a in enumerate(rows):
        for b in rows[i+1:]:
            if a['profile']!=b['profile']:continue
            by_time={}
            for sign,r in [(1,a),(-1,b)]:
                for event in r['events']:by_time[event['time']]=by_time.get(event['time'],0)+sign*event['expected_damage']
            delta=0;last=0
            for t,value in sorted(by_time.items()):
                delta+=value;sign=1 if delta>1e-9 else -1 if delta< -1e-9 else 0
                if sign and sign!=last:
                    changes.append(dict(profile=a['profile'],a=a['name'],b=b['name'],hit_time=t,
                        leader=a['name'] if sign>0 else b['name'],difference=abs(delta)))
                    last=sign
    return changes


def evaluate(document,ledger=None):
    for field in ['sandbox','mode','target','damage_unit','baseline_kind','provenance']:
        if not document.get(field):raise ValueError('Missing simulation metadata: '+field)
    if document['mode'] not in ('PvE','PvP'):raise ValueError('Unknown mode')
    if document['baseline_kind'] not in ('synthetic','measured','assumed'):raise ValueError('Unknown baseline kind')
    if 'baseline_sandbox' in document and document['baseline_sandbox']!=document['sandbox']:raise ValueError('Baseline sandbox mismatch')
    builds=document['builds'];profiles=document.get('profiles',[{'id':'declared'}])
    if not builds or not profiles or len(builds)>100 or len(profiles)>20:raise ValueError('Provide 1..100 candidates and 1..20 profiles')
    if len({b['name'] for b in builds})!=len(builds):raise ValueError('Build names must be unique')
    unique(profiles,'profiles')
    trials=integer(document.get('stochastic_trials',1),'stochastic trials',1,2000)
    event_budget=0
    for build in builds:
        weapon_map={w['id']:w for w in build.get('weapons',[])}
        ability_map={w['id']:w for w in build.get('abilities',[])}
        count=len(build.get('survival',{}).get('events',[]))
        for action in build.get('actions',[]):
            spec=weapon_map.get(action.get('weapon'),{}) if action['type']=='fire' else ability_map.get(action.get('ability'),{}) if action['type']=='cast' else {}
            count+=action.get('count',1)*max(1,sum(len(c.get('offsets',[0])) for c in spec.get('components',[])))
        event_budget+=count*trials*len(profiles)
    if event_budget>2000000:raise ValueError('Estimated event/ensemble budget exceeded')
    if trials*len(builds)*len(profiles)>10000:raise ValueError('Ensemble budget exceeded')
    rows=[]
    for profile in profiles:
        for build in builds:
            samples=[Simulation(dict(document,_trial=i),build,profile,ledger).run() for i in range(trials)]
            row=samples[0]
            if document.get('stochastic_trials'):
                for result in samples:row['evidence_used'].update(result['evidence_used'])
                def percentile(values,p):
                    v=sorted(values);return v[round((len(v)-1)*p)]
                for wi,window in enumerate(row['windows']):
                    values=[r['windows'][wi]['expected_damage'] for r in samples]
                    mean=math.fsum(values)/trials
                    window.update(expected_damage=mean,dps=mean/window['seconds'],p10=percentile(values,.1),p50=percentile(values,.5),p90=percentile(values,.9))
                curve={}
                for result in samples:
                    for event in result['events']:curve[event['time']]=curve.get(event['time'],0)+event['expected_damage']/trials
                row['events']=[dict(time=t,expected_damage=d) for t,d in sorted(curve.items())]
                row['ensemble']=dict(trials=trials,seed=document.get('seed',0),
                    survival_probability=sum(r['survival']['alive'] for r in samples if r['survival'])/trials if row['survival'] else None,
                    note='Mean curves and window quantiles; resource/effect/survival traces are trial 0, not ensemble means. Finite Monte Carlo estimate, not exact probability.')
                row['ttk_kind']='sample-0 realization only; not ensemble expected TTK'
            rows.append(row)
    return dict(schema_version=1,sandbox=document['sandbox'],mode=document['mode'],target=document['target'],damage_unit=document['damage_unit'],
        duration=document['duration'],results=rows,lead_changes=lead_changes(rows),
        convention='[0,T); equal-time incoming/healing signals before damage, hit procs after simultaneous damage; effects [start,end). In-flight attacks survive actor death.',
        limitations=['Declared model only, not an exhaustive game simulator or legal-loadout certification.',
            'Probabilistic hits contribute expected damage but do not deterministically proc threshold effects.',
            'Sequential charge regeneration; no inferred enemy AI, random loot, hidden engine rounding or unmodeled frame constraints.'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('scenario');p.add_argument('--ledger');p.add_argument('--out');p.add_argument('--summary',action='store_true')
    a=p.parse_args()
    def run():
        r=evaluate(load(a.scenario),load(a.ledger) if a.ledger else None)
        if a.summary:
            for x in r['results']:
                for key in ['events','fire_events','energy_events','effect_activations']:x.pop(key,None)
        return r
    cli_error(p,lambda:emit(run(),a.out))


if __name__=='__main__':main()
