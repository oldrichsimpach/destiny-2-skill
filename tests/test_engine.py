import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'destiny-2/scripts'))
from evidence import Ledger,Resolver
import simulate
import survivability
import optimize


def scenario():
    return dict(sandbox='test-v1',mode='PvE',target={'id':'synthetic target'},damage_unit='u',
        baseline_kind='synthetic',provenance='hand-computed test, not game measurements',duration=11,
        windows_seconds=[1,5,10,11],builds=[dict(name='A',initial_weapon='gun',weapons=[dict(id='gun',ammo=5,
            magazine=2,recovery_seconds=1,reload_seconds=3,components=[dict(id='hit',kind='weapon_combined',body=100)])],
            actions=[dict(type='fire',weapon='gun',count=5,auto_reload=True)])])


def effect(id='boost',**kwargs):
    return dict(id=id,kind='damage',category='empower',stacking='max',factor=2,duration_seconds=2,
        components=['weapon_combined'],**kwargs)


class RotationBehavior(unittest.TestCase):
    def row(self,s):return simulate.evaluate(s)['results'][0]

    def test_ammo_reload_and_half_open_windows(self):
        r=self.row(scenario())
        self.assertEqual([e['time'] for e in r['events']],[0,1,5,6,10])
        self.assertEqual([x['expected_damage'] for x in r['windows']],[100,200,400,500])
        self.assertEqual(r['ammo']['gun']['spent'],5)

    def test_zero_ammo_and_explicit_reload_required(self):
        s=scenario();s['builds'][0]['weapons'][0]['ammo']=0
        self.assertEqual(self.row(s)['events'],[])
        s=scenario();s['builds'][0]['actions'][0]['auto_reload']=False
        with self.assertRaises(ValueError):self.row(s)

    def test_reload_not_completed_after_phase_or_death(self):
        s=scenario();s['duration']=4;s['windows_seconds']=[4]
        r=self.row(s)
        self.assertEqual(r['ammo']['gun']['loaded'],0)
        s=scenario();b=s['builds'][0]
        b['survival']=dict(max_hp=100,events=[dict(time=3,kind='incoming',amount=100,damage_type='melee')])
        self.assertEqual(self.row(s)['ammo']['gun']['loaded'],0)

    def test_future_actions_do_not_rewind_after_long_wait(self):
        s=scenario();b=s['builds'][0];b['actions']=[dict(type='wait',seconds=20),dict(type='fire',weapon='gun',at=15)]
        self.assertEqual(self.row(s)['events'],[])

    def test_charge_projectile_delay_and_boundary(self):
        s=scenario();w=s['builds'][0]['weapons'][0];w['charge_seconds']=1;w['components'][0]['offsets']=[2]
        s['builds'][0]['actions'][0]['count']=1;s['windows_seconds']=[3,4]
        r=self.row(s)
        self.assertEqual(r['events'][0]['time'],3)
        self.assertEqual([v['expected_damage'] for v in r['windows']],[0,100])

    def test_trigger_after_hit_and_expiry(self):
        s=scenario();b=s['builds'][0];w=b['weapons'][0];w['ammo']=4;w['magazine']=4
        w['components'][0]['counts_for_triggers']=True
        b['effects']=[effect(trigger={'on':'hit','count':2},refreshable=False)]
        r=self.row(s)
        self.assertEqual([v['expected_damage'] for v in r['events']],[100,100,200,100])
        self.assertEqual(r['effect_activations'][0]['time'],1)

    def test_no_implicit_hit_count_from_damage_components(self):
        s=scenario();b=s['builds'][0];b['effects']=[effect(trigger={'on':'hit','count':1})]
        self.assertEqual(self.row(s)['effect_activations'],[])

    def test_max_within_category_product_between(self):
        s=scenario();b=s['builds'][0];b['effects']=[effect('low'),effect('high'),effect('surge')]
        b['effects'][0]['factor']=1.2;b['effects'][1]['factor']=1.25
        b['effects'][2].update(factor=1.22,category='surge')
        b['actions']=[{'type':'activate','effect':x['id']} for x in b['effects']]+[dict(type='fire',weapon='gun')]
        self.assertAlmostEqual(self.row(s)['events'][0]['expected_damage'],152.5)

    def test_effect_element_and_component_restrictions(self):
        s=scenario();b=s['builds'][0];b['effects']=[effect(element='Arc')]
        b['weapons'][0]['components'][0]['element']='Solar'
        b['actions']=[dict(type='activate',effect='boost'),dict(type='fire',weapon='gun')]
        self.assertEqual(self.row(s)['events'][0]['expected_damage'],100)

    def test_fire_snapshot_vs_hit_snapshot(self):
        s=scenario();b=s['builds'][0];b['effects']=[effect()];b['effects'][0]['duration_seconds']=1
        c=b['weapons'][0]['components'][0];c['offsets']=[1]
        b['actions']=[dict(type='activate',effect='boost'),dict(type='fire',weapon='gun')]
        self.assertEqual(self.row(s)['events'][0]['expected_damage'],100)
        c['snapshot']='fire'
        self.assertEqual(self.row(s)['events'][0]['expected_damage'],200)

    def test_movement_and_measured_range(self):
        s=scenario();s['profiles']=[dict(id='moving',movement_windows=[[1,3]],distance_m=15)]
        c=s['builds'][0]['weapons'][0]['components'][0]
        c.update(falloff_points=[[10,1],[20,.5]],falloff_interpolation='linear')
        s['builds'][0]['actions'][0]['count']=2
        r=self.row(s)
        self.assertEqual([x['time'] for x in r['events']],[0,3])
        self.assertEqual([x['expected_damage'] for x in r['events']],[75,75])
        s['profiles'][0]['distance_m']=21
        with self.assertRaises(ValueError):self.row(s)

    def test_stowed_refill_conserves_total_ammo(self):
        s=scenario();b=s['builds'][0];w=b['weapons'][0]
        w['refill']=dict(scope='stowed',delay_seconds=2,rounds_per_tick=2,capacity_rounds=2)
        b['weapons'].append(dict(id='other',ammo=1,magazine=1,recovery_seconds=1,components=[dict(id='x',kind='weapon_combined',body=1)]))
        b['actions']=[dict(type='fire',weapon='gun',count=2),dict(type='equip',weapon='other'),dict(type='wait',seconds=2),dict(type='fire',weapon='gun',count=2)]
        r=self.row(s)
        self.assertEqual(r['ammo']['gun']['spent'],4);self.assertEqual(r['ammo']['gun']['total_left'],1)
        self.assertEqual(r['refill_events'][0]['rounds_loaded'],2)

    def test_idle_overflow_uses_reserves_not_generated_ammo(self):
        s=scenario();b=s['builds'][0];w=b['weapons'][0]
        w['refill']=dict(scope='not_firing',delay_seconds=1,repeat_seconds=1,rounds_per_tick=1,capacity_rounds=4)
        b['actions']=[dict(type='wait',seconds=2),dict(type='fire',weapon='gun',count=4)]
        r=self.row(s);self.assertEqual(r['ammo']['gun']['spent'],4)
        self.assertEqual(r['ammo']['gun']['total_left'],1)

    def test_pickup_respects_capacity_and_balance(self):
        s=scenario();b=s['builds'][0]
        b['actions']=[dict(type='fire',weapon='gun'),dict(type='ammo_pickup',weapon='gun',rounds=99)]
        r=self.row(s);a=r['ammo']['gun']
        self.assertEqual(a['picked_up'],1);self.assertEqual(a['total_left'],5)
        self.assertEqual(5+a['picked_up']-a['spent'],a['total_left'])

    def test_death_stops_actions_but_inflight_damage_lands(self):
        s=scenario();b=s['builds'][0]
        b['survival']=dict(max_hp=100,events=[dict(time=1,kind='incoming',amount=100,damage_type='melee')])
        b['weapons'][0]['components'][0]['offsets']=[2]
        r=self.row(s)
        self.assertEqual(r['survival']['death_time'],1)
        self.assertEqual(len(r['fire_events']),1);self.assertEqual(r['events'][0]['time'],2)

    def test_rank_reversal_is_discrete(self):
        s=scenario();s['duration']=10;s['windows_seconds']=[1,10]
        a=s['builds'][0];a['weapons'][0].update(ammo=1,magazine=1);a['weapons'][0]['components'][0]['body']=400
        b=copy.deepcopy(a);b['name']='B';b['weapons'][0].update(ammo=10,magazine=10);b['weapons'][0]['components'][0]['body']=100
        b['actions'][0]['count']=10;s['builds'].append(b)
        r=simulate.evaluate(s)
        self.assertEqual([x['leader'] for x in r['lead_changes']],['A','B'])
        self.assertEqual(r['lead_changes'][-1]['hit_time'],4)

    def test_nonfinite_and_bad_category_rejected(self):
        s=scenario();s['builds'][0]['weapons'][0]['components'][0]['body']=float('nan')
        with self.assertRaises(ValueError):self.row(s)

    def test_source_factor_scope_and_category_cannot_be_repurposed(self):
        from test_evidence_legality_audit import ledger
        doc=ledger();record=doc['records'][0]
        record.update(unit='factor',value=1.2,stacking_group='empower')
        s=scenario();s['satisfied_conditions']=['target verified'];b=s['builds'][0]
        b['effects']=[effect()];b['effects'][0]['factor']={'claim':'a'}
        b['actions']=[dict(type='activate',effect='boost'),dict(type='fire',weapon='gun')]
        self.assertEqual(simulate.evaluate(s,doc)['results'][0]['events'][0]['expected_damage'],120)
        b['effects'][0]['category']='independent'
        with self.assertRaises(ValueError):simulate.evaluate(s,doc)
        b['effects'][0]['category']='empower';b['effects'][0]['components']=['ability']
        with self.assertRaises(ValueError):simulate.evaluate(s,doc)
        b['effects']=[];b['actions']=[dict(type='fire',weapon='gun')];s['target']['damage_scalar']={'claim':'a'}
        with self.assertRaises(ValueError):simulate.evaluate(s,doc)
        s=scenario();s['builds'][0]['effects']=[effect('a'),effect('b')];s['builds'][0]['effects'][1]['stacking']='product'
        with self.assertRaises(ValueError):self.row(s)


class AbilityBehavior(unittest.TestCase):
    def setup(self):
        s=scenario();b=s['builds'][0];b['weapons']=[];b.pop('initial_weapon')
        b['abilities']=[dict(id='grenade',cooldown_seconds=10,cast_seconds=1,initial_energy=0,components=[dict(id='explosion',kind='ability',body=100)])]
        b['actions']=[dict(type='cast',ability='grenade')]
        return s,b

    def test_first_cast_cannot_fund_itself(self):
        s,b=self.setup();b['effects']=[dict(id='refund',kind='instant',trigger={'on':'cast'},energy_grants=[dict(ability='grenade',amount=1)])]
        with self.assertRaises(ValueError):simulate.evaluate(s)

    def test_passive_recharge_and_resource_conservation(self):
        s,b=self.setup();s['duration']=12;s['windows_seconds']=[12];b['actions'][0]['auto_wait']=True
        r=simulate.evaluate(s)['results'][0];a=r['ability_resources']['grenade']
        self.assertAlmostEqual(a['final_energy'],.2)
        self.assertAlmostEqual(a['initial_energy']+a['passive_gained']+a['grants_gained']-a['spent'],a['final_energy'])

    def test_chunk_and_class_scalars_apply_once(self):
        s,b=self.setup();b['abilities'][0]['initial_energy']=1
        b['effects']=[dict(id='grant',kind='instant',trigger={'on':'cast'},energy_grants=[dict(ability='grenade',amount=.2,chunk_scalar=.5,class_mod_scalar=.25)])]
        r=simulate.evaluate(s)['results'][0]
        self.assertAlmostEqual(r['energy_events'][1]['actual'],.025)

    def test_recharge_multiplier_expires_within_wait(self):
        s,b=self.setup();s['duration']=9;s['windows_seconds']=[9]
        b['effects']=[dict(id='regen',kind='recharge',category='speed',stacking='max',factor=2,duration_seconds=2,ability_ids=['grenade'])]
        b['actions']=[dict(type='activate',effect='regen'),dict(type='cast',ability='grenade',auto_wait=True)]
        r=simulate.evaluate(s)['results'][0]
        self.assertAlmostEqual(r['energy_events'][0]['time'],8)


class SurvivalBehavior(unittest.TestCase):
    def model(self,**kwargs):
        s=scenario();s['survival']=dict(max_hp=200,events=[],**kwargs);return s

    def test_same_group_max_independent_groups_product(self):
        dr=[dict(id='a',fraction=.3,independence_group='armor',damage_types=['solar'],end=20),
            dict(id='b',fraction=.5,independence_group='armor',damage_types=['solar'],end=20),
            dict(id='c',fraction=.4,independence_group='other',damage_types=['solar'],end=20)]
        s=self.model(resistances=dr);s['survival']['events']=[dict(time=0,kind='incoming',amount=100,damage_type='solar')]
        self.assertAlmostEqual(survivability.evaluate(s)['hp'],170)

    def test_overshield_dr_and_overflow_conversion(self):
        s=self.model(overshields=[dict(id='void',capacity=50,dr=.5,start=0,end=20)],
            resistances=[dict(id='armor',fraction=.2,independence_group='armor',damage_types=['solar'],end=20)])
        s['survival']['events']=[dict(time=0,kind='incoming',amount=200,damage_type='solar')]
        self.assertAlmostEqual(survivability.evaluate(s)['hp'],140)

    def test_type_expiry_and_healing_cannot_revive(self):
        s=self.model(resistances=[dict(id='x',fraction=1,independence_group='invuln',damage_types=['void'],end=1)])
        s['survival']['events']=[dict(time=0,kind='incoming',amount=1000,damage_type='void'),
            dict(time=1,kind='incoming',amount=200,damage_type='void'),dict(time=1,kind='heal',amount=200)]
        r=survivability.evaluate(s)
        self.assertEqual(r['death_time'],1);self.assertEqual(r['hp'],0)


class StochasticAndCandidates(unittest.TestCase):
    def test_seeded_stochastic_is_reproducible_and_procs_on_realized_hits(self):
        s=scenario();s['stochastic_trials']=30;s['seed']=42
        b=s['builds'][0];b['weapons'][0]['components'][0].update(hit_probability=.5,counts_for_triggers=True)
        b['effects']=[effect(trigger={'on':'hit','count':1})]
        a=simulate.evaluate(s);z=simulate.evaluate(s)
        self.assertEqual(a['results'][0]['windows'],z['results'][0]['windows'])
        self.assertGreater(a['results'][0]['windows'][-1]['expected_damage'],0)
        self.assertEqual(a['results'][0]['skipped_procs'],[])

    def test_expected_hits_never_silently_guarantee_proc(self):
        s=scenario();b=s['builds'][0];b['effects']=[effect(trigger={'on':'hit','count':1})]
        b['weapons'][0]['components'][0].update(hit_probability=.5,counts_for_triggers=True)
        r=simulate.evaluate(s)['results'][0]
        self.assertTrue(r['skipped_procs']);self.assertFalse(r['effect_activations'])

    def test_inventory_filters_exact_instances_and_preserves_unknown_legality(self):
        s=scenario();s['builds'][0]['loadout']={'items':[dict(item_hash='10',item_instance_id='owned')]}
        b=copy.deepcopy(s['builds'][0]);b['name']='Not owned';b['loadout']['items'][0]['item_instance_id']='missing';s['builds'].append(b)
        r=optimize.optimize(s,dict(instances=[dict(item_hash='10',item_instance_id='owned')]))
        self.assertEqual(r['frontiers'][0]['pareto_front'],['A'])
        self.assertEqual(r['excluded'][0]['name'],'Not owned')
        self.assertEqual(r['legality']['A']['status'],'not_checked')


if __name__=='__main__':unittest.main()
