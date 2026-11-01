import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'destiny-2/scripts'))
from evidence import Ledger,Resolver
import audit_sources
import legality
import workbooks


def ledger():
    return {'records':[dict(id='a',entity='Precision Scout Rifle',field='damage',value=100,unit='u',mode='PvE',
        components=['weapon_combined'],status='verified_for_scope',applies_to=['test-v1'],conditions=['target verified'],
        provenance=dict(source_id='s',url='https://example.test/source',locator='Data!B3',retrieved_at='2026-11-01',watch=[dict(sheet='Data',range='A3:C3')])),
        dict(id='unrelated',entity='Other',field='damage',value=20,unit='u',mode='PvE',components=['weapon_combined'],
        status='verified_for_scope',applies_to=['test-v1'],conditions=[],provenance=dict(source_id='s',url='https://example.test/source',
        locator='Data!B9',retrieved_at='2026-11-01',watch=[dict(sheet='Data',range='A9:C9')]))]}


class EvidenceBehavior(unittest.TestCase):
    def context(self):return dict(sandbox='test-v1',mode='PvE',satisfied_conditions=['target verified'])

    def test_patch_mode_unit_component_conditions_are_separate(self):
        l=Ledger(ledger());ctx=self.context()
        self.assertEqual(l.resolve('a',ctx,'u','weapon_combined')[0],100)
        for context,unit,component in [(dict(ctx,sandbox='test-v2'),'u','weapon_combined'),
            (dict(ctx,mode='PvP'),'u','weapon_combined'),(ctx,'raw hp','weapon_combined'),(ctx,'u','ability'),
            (dict(ctx,satisfied_conditions=[]),'u','weapon_combined')]:
            with self.assertRaises(ValueError):l.resolve('a',context,unit,component)

    def test_conflict_selection_is_explicit_and_conditional(self):
        doc=ledger();doc['records'][0].update(status='conflicted',conflict_group='conflict')
        l=Ledger(doc);ctx=dict(self.context(),allow_partial=True)
        with self.assertRaises(ValueError):l.resolve('a',ctx,'u')
        value,_,reasons=l.resolve('a',dict(ctx,conflict_choices={'conflict':'a'}),'u')
        self.assertEqual(value,100);self.assertTrue(reasons)

    def test_unknown_and_historical_are_not_current_coefficients(self):
        doc=ledger();doc['records'][0].update(value=None,status='unknown')
        with self.assertRaises(ValueError):Ledger(doc).resolve('a',self.context(),'u')
        doc['records'][0].update(value=100,status='historical_stale',applies_to=['old'])
        with self.assertRaises(ValueError):Ledger(doc).resolve('a',dict(self.context(),allow_partial=True),'u')

    def test_bare_measured_numbers_require_assumption_opt_in(self):
        ctx=dict(self.context(),baseline_kind='measured')
        with self.assertRaises(ValueError):Resolver(ctx,ledger()).value(3,'seconds','reload')
        r=Resolver(dict(ctx,allow_assumptions=True),ledger());r.value(3,'seconds','reload')
        self.assertEqual(r.report()['result_kind'],'conditional')


class FakeManifest:
    metadata={'version':'fixture-v1','retrieved_utc':'2026-11-01'}
    def __init__(self):
        self.defs={
          '10':dict(itemType=3,classType=3,equippingBlock=dict(equipmentSlotTypeHash=1,uniqueLabelHash=77),
             inventory={'recipeItemHash':100},sockets={'socketEntries':[dict(randomizedPlugSetHash=20)]}),
          '11':dict(itemType=3,classType=3,equippingBlock=dict(equipmentSlotTypeHash=2,uniqueLabelHash=77),sockets={'socketEntries':[]}),
          '12':dict(itemType=2,classType=1,equippingBlock=dict(equipmentSlotTypeHash=3),sockets={'socketEntries':[]}),
          '100':dict(itemType=30,sockets={'socketEntries':[dict(reusablePlugSetHash=21)]})}
        self.sets={'20':dict(reusablePlugItems=[dict(plugItemHash=30,currentlyCanRoll=True),dict(plugItemHash=31,currentlyCanRoll=False)]),
                   '21':dict(reusablePlugItems=[dict(plugItemHash=40,craftingRequirements={'unlockRequirements':['level']})])}
    def get(self,kind,key):return (self.sets if kind=='DestinyPlugSetDefinition' else self.defs).get(str(key))


class LegalityBehavior(unittest.TestCase):
    def doc(self):return dict(class_type=1,sandbox='fixture',manifest_version='fixture-v1',required_buckets=[1],items=[dict(item_hash='10',plugs=[dict(socket=0,plug_hash='30')])])
    def validate(self,d,rules=None):return legality.validate(d,FakeManifest(),rules)

    def test_membership_is_not_full_equipability(self):
        r=self.validate(self.doc())
        self.assertEqual(r['status'],'structurally_compatible_runtime_unverified')
        self.assertTrue(any(x['status']=='supported' for x in r['checks']))
        self.assertTrue(any(x['scope']=='server' and x['status']=='unknown' for x in r['checks']))

    def test_wrong_column_and_nonrolling_perk_are_rejected_for_new_roll(self):
        for ph in ['999','31']:
            d=self.doc();d['items'][0]['plugs'][0]['plug_hash']=ph
            self.assertEqual(self.validate(d)['status'],'invalid')

    def test_slots_class_and_unique_equip_labels(self):
        d=self.doc();d['items'].append(dict(item_hash='11'))
        self.assertEqual(self.validate(d)['status'],'invalid')
        d=self.doc();d['class_type']=0;d['items'].append(dict(item_hash='12'))
        self.assertEqual(self.validate(d)['status'],'invalid')
        d=self.doc();d['items'].append(copy.deepcopy(d['items'][0]))
        self.assertEqual(self.validate(d)['status'],'invalid')

    def test_recipe_is_not_equippable_and_crafting_needs_dynamic_evidence(self):
        d=self.doc();d['items'][0]['item_hash']='100'
        self.assertEqual(self.validate(d)['status'],'invalid')
        d=self.doc();d['items'][0]['plugs'][0].update(path='crafting',plug_hash='40')
        r=self.validate(d)
        self.assertEqual(r['status'],'structurally_compatible_runtime_unverified')
        self.assertTrue(any('crafting requirements' in x['message'] for x in r['checks']))

    def test_owned_current_plug_can_be_older_than_roll_pool(self):
        d=self.doc();d['purpose']='owned_equipment'
        d['items'][0].update(owned_instance=dict(item_hash='10',item_instance_id='instance',provenance='supplied runtime snapshot',retrieved_at='2026-11-01',
            sockets={'0':dict(plug_hash='999',is_enabled=True)}))
        d['items'][0]['plugs'][0].update(path='owned',plug_hash='999')
        r=self.validate(d)
        self.assertNotEqual(r['status'],'invalid')
        self.assertTrue(any('active plug observed' in x['message'] for x in r['checks']))

    def test_fragment_slots_artifact_era_and_energy_budgets(self):
        d=self.doc();d['subclass']=dict(id='solar',aspects=['aspect'],fragments=['a','b','c'])
        d['artifact']=dict(id='wrong-era',mods=['mod','mod'])
        d['armor_mods']=[dict(slot='head',energy_capacity=3,mods=[dict(energy_cost=4)])]
        rules=dict(sandbox='fixture',class_type=1,provenance='synthetic test rules',max_aspects=2,
            aspects=[dict(id='aspect',subclasses=['solar'],fragment_slots=2)],fragments={'solar':['a','b','c']},
            artifact=dict(id='era',budget=1,mods={'mod':{'cost':1}}))
        r=self.validate(d,rules)
        self.assertEqual(r['status'],'invalid')
        scopes={x['scope'] for x in r['checks'] if x['status']=='invalid'}
        self.assertTrue({'subclass','artifact','armor_mods'}<=scopes)

    def test_audited_armor_cost_slot_and_socket_rules_override_caller_numbers(self):
        d=self.doc();d['subclass']=dict(id='solar',aspects=[],fragments=[])
        d['armor_mods']=[dict(slot='head',energy_capacity=100,mods=[dict(id='leg-only',energy_cost=0)])]
        rules=dict(sandbox='fixture',class_type=1,provenance='synthetic rule fixture',max_aspects=2,aspects=[],fragments={'solar':[]},
            armor=dict(slots={'head':dict(energy_capacity=3,socket_count=4)},mods={'leg-only':dict(allowed_slots=['legs'],energy_cost=4,max_copies=1)}))
        r=self.validate(d,rules)
        self.assertEqual(r['status'],'invalid')
        messages=[x['message'] for x in r['checks']]
        self.assertIn('Caller mod cost differs from audited rule',messages)
        self.assertIn('Mod not permitted in armor slot',messages)
        self.assertIn('Energy budget exceeded',messages)


class SourceChangeBehavior(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'tests');self.dir=Path(self.temp.name)

    def tearDown(self):
        assert self.dir.resolve().is_relative_to((ROOT/'tests').resolve())
        self.temp.cleanup()

    def fixture(self,path,value=100,strike=False):
        import openpyxl
        from openpyxl.styles import Font
        w=openpyxl.Workbook();s=w.active;s.title='Data';s['B3']=value;s['B3'].font=Font(strike=strike);s['B9']=20
        w.save(path);w.close()

    def test_value_and_strikethrough_changes_invalidate_only_dependent_claim(self):
        a,b=self.dir/'a.xlsx',self.dir/'b.xlsx'
        self.fixture(a);self.fixture(b,strike=True)
        old=audit_sources.snapshot(a,'s');new=audit_sources.snapshot(b,'s')
        r=audit_sources.diff(old,new,ledger())
        self.assertEqual(r['affected_claims'],['a'])
        self.assertEqual(r['changed_cell_counts'],{'Data':1})

    def test_unchanged_export_does_not_flag_claims(self):
        a=self.dir/'a.xlsx';self.fixture(a);s=audit_sources.snapshot(a,'s')
        r=audit_sources.diff(s,s,ledger())
        self.assertFalse(r['file_changed']);self.assertEqual(r['affected_claims'],[])

    def test_patch_mentions_flag_results_without_changing_coefficients(self):
        p=self.dir/'result.json';p.write_text(json.dumps({'results':[{'evidence_used':{'a':{}}}]}))
        original=ledger();doc=dict(patch='test-v2',published_at='2026-11-02',url='https://www.bungie.net/7/en/News/Article/test',text='Precision Scout Rifle damage adjusted.')
        r=audit_sources.patch_review(doc,original,[p])
        self.assertEqual(r['affected_claims'],['a']);self.assertEqual(len(r['affected_results']),1)
        self.assertEqual(original['records'][0]['value'],100)
        doc['url']='https://bungie.net.evil.test/patch'
        with self.assertRaises(ValueError):audit_sources.patch_review(doc,original)

    def test_persistent_invalidation_blocks_later_numeric_use(self):
        p=self.dir/'state.json'
        audit_sources.update_review_state(dict(affected_claims=['a'],source_id='s'),p)
        r=Resolver(dict(sandbox='test-v1',mode='PvE',satisfied_conditions=['target verified'],review_state=str(p)),ledger())
        with self.assertRaises(ValueError):r.value({'claim':'a'},'u','damage','weapon_combined')

    def test_array_formula_fingerprint_is_stable_and_serializable(self):
        import openpyxl
        from openpyxl.worksheet.formula import ArrayFormula
        p=self.dir/'array.xlsx';self.fixture(p)
        w=openpyxl.load_workbook(p);w['Data']['C3']=ArrayFormula(ref='C3:C3',text='=SUM(B3:B3)');w.save(p);w.close()
        a=audit_sources.snapshot(p,'s');b=audit_sources.snapshot(p,'s')
        self.assertFalse(audit_sources.diff(a,b,ledger())['semantic_changes'])
        self.assertEqual(a['sheets']['Data']['cells']['C3'],b['sheets']['Data']['cells']['C3'])

    def test_workbook_reader_preserves_array_formula_text(self):
        import openpyxl
        from openpyxl.worksheet.formula import ArrayFormula
        p=self.dir/'boss.xlsx';w=openpyxl.Workbook();s=w.active;s.title='Weapons'
        s['B2']='Type';s['C2']='Subtype';s['U2']='Patch';s['B3']='Test';s['C3']='Adaptive';s['U3']='test-v1';s['L3']=100
        s['D3']=ArrayFormula(ref='D3:D3',text='=SUM(L3:L3)');w.save(p);w.close()
        row=workbooks.row('boss','Weapons',3,p)
        self.assertEqual(row['cells']['D']['formula']['text'],'=SUM(L3:L3)')
        json.dumps(row,allow_nan=False)
        candidate=workbooks.baseline('boss','Weapons',3,'L','weapon_combined',p)
        self.assertIn('verify new snapshot identity and schema',candidate['conditions'])
        self.assertEqual(candidate['provenance']['retrieved_at'],'unknown')
        self.assertIn('verify source retrieval date',candidate['conditions'])

    def test_import_validates_date_before_replacement_and_archives_old_snapshot(self):
        import openpyxl,hashlib,io
        from unittest.mock import patch
        from contextlib import redirect_stdout,redirect_stderr
        target_root=self.dir/'skill';dest=target_root/'assets/private/boss.xlsx';dest.parent.mkdir(parents=True)
        def save(path,value):
            w=openpyxl.Workbook();s=w.active;s.title='Weapons';s['U2']='Patch';s['L3']=value;w.save(path);w.close()
        new=self.dir/'new.xlsx';save(dest,100);save(new,200)
        before=hashlib.sha256(dest.read_bytes()).hexdigest()
        meta=dict(url='https://example.test/boss',sha256=before,retrieved_at='2026-11-01',local_path='assets/private/boss.xlsx',
            required_sheets=['Weapons'],identity_cells=[dict(sheet='Weapons',cell='U2',value='Patch')])
        with patch.object(workbooks,'ROOT',target_root),patch.object(workbooks,'catalog',lambda:{'sources':{'boss':meta}}):
            with patch.object(sys,'argv',['workbooks.py','boss','import',str(new),'--retrieved-at','bad']),redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):workbooks.main()
            self.assertEqual(hashlib.sha256(dest.read_bytes()).hexdigest(),before)
            with patch.object(sys,'argv',['workbooks.py','boss','import',str(new),'--retrieved-at','2026-11-02']),redirect_stdout(io.StringIO()):workbooks.main()
        archived=list((dest.parent/'history').glob('*.xlsx'))
        self.assertEqual(len(archived),1);self.assertEqual(hashlib.sha256(archived[0].read_bytes()).hexdigest(),before)
        receipts=json.loads((dest.parent/'workbook-receipts.json').read_text())
        self.assertEqual(next(iter(receipts.values()))['retrieved_at'],'2026-11-02')


if __name__=='__main__':unittest.main()
