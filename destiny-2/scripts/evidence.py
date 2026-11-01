"""Search and resolve patch/unit-specific claims; preserve conflicts and uncertainty."""
import argparse
from engine_common import ROOT, load, emit, finite, unique, cli_error, default_review_state

DEFAULT = ROOT/'data/claims.json'
ALLOWED = {'verified_for_scope','community_measurement','partially_verified','assumed',
           'historical_stale','unknown','conflicted','hypothetical'}


class Ledger:
    def __init__(self, document=None):
        self.document = document if document is not None else load(DEFAULT)
        self.records = unique(self.document['records'], 'claims')
        for key, r in self.records.items():
            for field in ['entity','field','unit','status','provenance','applies_to','conditions']:
                if field not in r:
                    raise ValueError(f'{key}: missing {field}')
            if r['status'] not in ALLOWED:
                raise ValueError(f'{key}: unknown status')
            p = r['provenance']
            for field in ['source_id','url','locator','retrieved_at']:
                if not p.get(field):
                    raise ValueError(f'{key}: missing provenance {field}')

    def conflicts(self):
        groups = {}
        for r in self.records.values():
            if r.get('conflict_group'):
                groups.setdefault(r['conflict_group'], []).append(r['id'])
        return [{'id': k, 'alternatives': v, 'resolution': 'unresolved; select explicit variant and retain conditional label'}
                for k, v in groups.items()]

    def resolve(self, key, context, unit, component=None):
        if key not in self.records:
            raise ValueError('Unknown claim: ' + key)
        r = self.records[key]
        if r['value'] is None or r['status'] in ('unknown','hypothetical'):
            raise ValueError('Claim is not a usable numerical observation: ' + key)
        if r['unit'] != unit:
            raise ValueError(f'{key}: unit {r["unit"]!r} does not match {unit!r}')
        if r.get('mode') not in (context.get('mode'), 'both'):
            raise ValueError('Claim mode mismatch: ' + key)
        if context['sandbox'] not in r['applies_to']:
            raise ValueError('Claim sandbox not established: ' + key)
        if component and component not in r.get('components', []):
            raise ValueError('Claim component mismatch: ' + key)
        reasons = []
        if r['status'] != 'verified_for_scope':
            if not context.get('allow_partial'):
                raise ValueError('Explicit allow_partial required: ' + key)
            reasons.append(r['status'])
        if r.get('conflict_group'):
            if context.get('conflict_choices', {}).get(r['conflict_group']) != key:
                raise ValueError('Unresolved conflict needs an explicit variant: ' + r['conflict_group'])
            reasons.append('unresolved conflict variant')
        missing = [x for x in r['conditions'] if x not in context.get('satisfied_conditions', [])]
        if missing:
            raise ValueError(f'{key}: conditions not declared satisfied: {missing}')
        return finite(r['value'], key), r, reasons


class Resolver:
    def __init__(self, context, document=None):
        self.context = context
        self.ledger = Ledger(document)
        state_path=context.get('review_state')
        if state_path:self.review=load(state_path)
        elif default_review_state().exists():self.review=load(default_review_state())
        else:self.review={}
        self.used = {}
        self.assumptions = []
        self.conditional = []

    def value(self, spec, unit, label, component=None, low=0, high=None):
        if isinstance(spec, dict) and 'claim' in spec:
            if self.review.get('claims',{}).get(spec['claim'],{}).get('status')=='needs_review':
                raise ValueError('Claim invalidated by source/patch review: '+spec['claim'])
            value, record, reasons = self.ledger.resolve(spec['claim'], self.context, unit, component)
            self.used[record['id']] = record['provenance']
            self.conditional.extend(f'{record["id"]}: {r}' for r in reasons)
        else:
            if isinstance(spec, dict):
                if spec.get('unit') != unit or not spec.get('provenance'):
                    raise ValueError(label + ': literal requires matching unit and provenance')
                value = spec['value']
                note = spec['provenance']
            else:
                value, note = spec, 'caller-supplied model input'
            if self.context.get('baseline_kind') != 'synthetic' and not self.context.get('allow_assumptions'):
                raise ValueError(label + ': unverified input requires allow_assumptions')
            self.assumptions.append({'field': label, 'unit': unit, 'value': value, 'provenance': note})
        return finite(value, label, low, high)

    def report(self):
        kind = ('synthetic' if self.context.get('baseline_kind') == 'synthetic'
                else 'conditional' if self.assumptions or self.conditional else 'sourced_model')
        return dict(result_kind=kind, evidence_used=self.used, assumptions=self.assumptions,
                    qualifications=sorted(set(self.conditional)),
                    scope='Source checks are scoped evidence, not independent in-game validation or proof of legal equipment. Automatic invalidation covers referenced claims; literal inputs require manual re-review.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ledger')
    p.add_argument('--review-state')
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('search'); s.add_argument('query')
    sub.add_parser('conflicts')
    a = p.parse_args()
    def run():
        ledger = Ledger(load(a.ledger) if a.ledger else None)
        if a.command == 'conflicts':return ledger.conflicts()
        import json
        from pathlib import Path
        path=Path(a.review_state) if a.review_state else default_review_state()
        state=load(path).get('claims',{}) if path.exists() else {}
        return [dict(x,runtime_review=state.get(x['id'],{})) for x in ledger.records.values() if a.query.casefold() in json.dumps(x,ensure_ascii=False).casefold()]
    cli_error(p, lambda: emit(run()))


if __name__ == '__main__':main()
