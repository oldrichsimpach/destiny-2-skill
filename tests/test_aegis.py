import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import os
import sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('aegis',ROOT/'destiny-2/scripts/aegis.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)


class AegisBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import openpyxl
        cls.tmp=tempfile.TemporaryDirectory(dir=ROOT/'tests')
        cls.path=Path(cls.tmp.name)/'fixture.xlsx'
        w=openpyxl.Workbook();w.active.title='Status'
        w['Status'].append(['TAB','UPDATED','STATUS'])
        w['Status'].append(['Perks','2026-01-01','updated'])
        w['Status'].append(['Experimental','2024-09-09','future'])
        for name in ['Archetypes','Perks','Experimental','Exotic Armor (ignore)','Hidden','Shopping List','Origin Traits']:
            s=w.create_sheet(name);s.append(['TITLE']);s.append([None,'Name','Weapon'])
            s.append([None,'Test Effect','Source weapon',None,None,'1?% unknown'])
        w['Hidden'].sheet_state='hidden'
        w['Perks']['F3'].comment=openpyxl.comments.Comment('Keep trigger exception','Test')
        w['Archetypes']['C3']='Auto rifle'
        for cell,v in dict(H3=10,M3=.1,O3=600,P3=5,Q3=1,S3=.4,AI3=50/1.4).items():w['Archetypes'][cell]=v
        w.save(cls.path);w.close()

    @classmethod
    def tearDownClass(cls):
        assert Path(cls.tmp.name).resolve().is_relative_to((ROOT/'tests').resolve())
        cls.tmp.cleanup()

    def args(self,**kwargs):
        return argparse.Namespace(command='search',workbook=str(self.path),query='Test Effect',sheet=None,
            include_history=False,details=False,limit=20,**kwargs)

    def test_default_excludes_historical_ignored_and_hypothetical(self):
        result=a.run(self.args())
        self.assertEqual({r['sheet'] for r in result['results']},{'Perks','Origin Traits'})

    def test_explicit_history_is_labeled(self):
        args=self.args();args.include_history=True
        result=a.run(args)
        self.assertIn('historical',{x['status']['classification'] for x in result['results']})
        args.command='row';args.sheet='Exotic Armor (ignore)';args.row=3;args.include_history=False
        with self.assertRaises(ValueError):a.run(args)

    def test_exact_row_preserves_uncertain_text_comments_and_original(self):
        before=hashlib.sha256(self.path.read_bytes()).hexdigest()
        args=self.args();args.command='row';args.sheet='Perks';args.row=3
        result=a.run(args)
        self.assertEqual(result['cells']['F']['value'],'1?% unknown')
        self.assertEqual(result['cells']['F']['comment'],'Keep trigger exception')
        self.assertFalse(result['source']['audited_snapshot'])
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),before)

    def test_detail_search_matches_effect_but_name_search_does_not(self):
        args=self.args();args.query='unknown'
        self.assertEqual(a.run(args)['total'],0)
        args.details=True
        self.assertGreater(a.run(args)['total'],0)

    def test_missing_snapshot_returns_locator_only(self):
        args=self.args();args.workbook=str(Path(self.tmp.name)/'missing.xlsx');args.query='Cascade Point'
        result=a.run(args)
        self.assertTrue(result['index_only']);self.assertGreater(result['total'],0)
        self.assertNotIn('cells',result['results'][0])

    def test_arithmetic_detects_a_changed_cache(self):
        w=a.book(self.path)
        self.assertFalse(a.check_math(w)['mismatches'])
        w['Archetypes']['O3']=599
        self.assertEqual(a.check_math(w)['mismatches'][0]['cell'],'O3')
        w.close()

    def test_wrong_workbook_import_is_rejected(self):
        import openpyxl
        p=Path(self.tmp.name)/'wrong.xlsx';w=openpyxl.Workbook();w.save(p);w.close()
        args=self.args();args.command='import';args.file=str(p)
        with self.assertRaises(ValueError):a.run(args)

    def test_windows_legacy_stdout_still_produces_utf8_json(self):
        import openpyxl
        p=Path(self.tmp.name)/'unicode.xlsx'
        w=openpyxl.load_workbook(self.path);w['Perks']['F3']='✔ Unicode effect';w.save(p);w.close()
        env=dict(os.environ,PYTHONIOENCODING='cp1250')
        result=subprocess.run([sys.executable,str(ROOT/'destiny-2/scripts/aegis.py'),
            'row','--workbook',str(p),'--sheet','Perks','3'],capture_output=True,env=env)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout.decode('utf-8'))['cells']['F']['value'],'✔ Unicode effect')


if __name__=='__main__':unittest.main(verbosity=2)
