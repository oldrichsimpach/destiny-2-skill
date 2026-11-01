import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'destiny-2/scripts'))
import compare
import knowledge
import science_workbook


class NumericBehavior(unittest.TestCase):
    def test_strongest_empower_and_same_element_surge(self):
        result = knowledge.effect_multiplier(['radiant', 'well', 'surge-1', 'surge-3', 'tractor'],
                                             'PvE', '9.7.0.3', True)
        self.assertAlmostEqual(result['multiplier'], 1.25*1.22*1.30)
        self.assertEqual(result['groups']['empowering']['suppressed'], ['radiant'])
        self.assertEqual(result['groups']['weapon_surge']['suppressed'], ['surge-1'])

    def test_mode_changes_result(self):
        self.assertAlmostEqual(knowledge.effect_multiplier(['radiant','surge-3'], 'PvP','9.7.0.3',True)['multiplier'],1.1*1.055)

    def test_patch_and_uncertainty_are_not_silent(self):
        for args in [(['radiant'],'PvE','9.7.0.6',True), (['radiant'],'PvE','9.7.0.3',False),
                     (['well'],'PvP','9.7.0.3',True), (['radiant','radiant'],'PvE','9.7.0.3',True)]:
            with self.assertRaises(ValueError): knowledge.effect_multiplier(*args)

    def test_shot_and_reload_boundaries(self):
        self.assertEqual(list(compare.shots(0,2,1,3)),[])
        self.assertEqual(list(compare.shots(5,2,1,3)),[0,1,4,5,8])
        self.assertEqual(list(compare.shots(3,1,.5,2,first_hit=1)),[1,3,5])

    def scenario(self):
        return {'sandbox':'9.7.0.3','mode':'PvE','target':'synthetic static target',
            'damage_baseline':'synthetic units','provenance':'unit test, not Destiny measurements',
            'baseline_sandbox':'9.7.0.3','baseline_kind':'synthetic',
            'windows_seconds':[1,4,5,9], 'builds':[{'name':'finite ammo','events':[
                {'time':t,'body':100} for t in compare.shots(5,2,1,3)]}]}

    def test_event_window_and_cumulative_damage(self):
        row = compare.evaluate(self.scenario())['builds'][0]
        self.assertEqual([r['expected_damage'] for r in row['windows']],[100,200,300,500])

    def test_expected_crit_and_miss(self):
        s=self.scenario();s['builds'][0]['events']=[{'time':0,'body':100,'crit':200,'hit_probability':.8,'crit_given_hit':.25}]
        self.assertAlmostEqual(compare.evaluate(s)['builds'][0]['windows'][0]['expected_damage'],100)

    def test_nan_and_ability_buff_rejected(self):
        s=self.scenario();s['builds'][0]['events'][0]['body']=float('nan')
        with self.assertRaises(ValueError):compare.evaluate(s)

    def test_damage_baseline_patch_mismatch(self):
        s=self.scenario();s['baseline_sandbox']='8.1.5'
        with self.assertRaises(ValueError):compare.evaluate(s)
        s=self.scenario();s['builds'][0]['events'][0]['baseline_sandbox']='8.1.5'
        with self.assertRaises(ValueError):compare.evaluate(s)
        s=self.scenario();s['allow_partial']=True;s['builds'][0]['events'][0].update(
            effect_ids=['radiant'],component='ability',conditions_satisfied=True)
        with self.assertRaises(ValueError):compare.evaluate(s)

    def test_dr_uses_remaining_damage(self):
        r=compare.survival(200,[.5,.4])
        self.assertAlmostEqual(r['remaining_damage_factor'],.3)
        self.assertAlmostEqual(r['effective_hp'],200/.3)
        with self.assertRaises(ValueError):compare.survival(200,[1])


class SourceEvidence(unittest.TestCase):
    def test_all_citations_resolve(self):
        sources={r['id'] for r in knowledge.read('sources.json')['records']}
        for file in ['effects.json','facts.json','stat-samples.json']:
            for row in knowledge.read(file)['records']:
                self.assertIn(row['source_id'],sources)
                self.assertTrue(row['locator'])
                self.assertTrue(row['status'])

