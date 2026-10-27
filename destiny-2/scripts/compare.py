"""Finite-window, explicit-event comparison. No automatic game or loadout simulation."""
import argparse
import json
import math
from pathlib import Path

from knowledge import effect_multiplier


def number(value, label, minimum=0, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(label + ' must be a finite number')
    if value < minimum or (maximum is not None and value > maximum):
        raise ValueError(label + ' outside valid range')
    return value


def shots(ammo, magazine, interval, reload_gap, first_hit=0):
    """First shot at first_hit; reload_gap from a mag's last shot to next first shot."""
    for v, key in ((ammo, 'ammo'), (magazine, 'magazine')):
        number(v, key)
        if not isinstance(v, int) or (key == 'magazine' and v == 0) or v > 100000:
            raise ValueError(key + ' must be a bounded integer')
    number(interval, 'interval', minimum=1e-9)
    number(reload_gap, 'reload_gap', minimum=interval)
    number(first_hit, 'first_hit')
    t = first_hit
    for i in range(ammo):
        yield t
        t += reload_gap if (i+1) % magazine == 0 else interval


def survival(hp, independent_dr):
    number(hp, 'HP', minimum=1e-9)
    remaining = math.prod(1-number(r, 'DR', maximum=1) for r in independent_dr)
    if remaining == 0:
        raise ValueError('Invulnerability needs a time/state model; finite EHP undefined')
    return {'remaining_damage_factor': remaining, 'effective_hp': hp/remaining}


def evaluate(scenario):
    for key in ('sandbox', 'mode', 'target', 'damage_baseline', 'baseline_sandbox', 'baseline_kind', 'provenance'):
        if not scenario.get(key):
            raise ValueError('Missing scenario metadata: ' + key)
    if scenario['mode'] not in ('PvE', 'PvP'):
        raise ValueError('Invalid mode')
    if scenario['baseline_sandbox'] != scenario['sandbox']:
        raise ValueError('Damage baseline and scenario sandboxes differ')
    if scenario['baseline_kind'] not in ('synthetic', 'measured', 'assumed'):
        raise ValueError('baseline_kind must be synthetic, measured or assumed')
    windows = sorted(set(scenario['windows_seconds']))
    for t in windows:
        number(t, 'window', minimum=1e-9)
    if not windows:
        raise ValueError('At least one window required')
    output = []
    for build in scenario['builds']:
        events = build.get('events', [])
        if len(events) > 100000:
            raise ValueError('Too many events')
        timeline = []
        for event in events:
            if event.get('baseline_sandbox', scenario['baseline_sandbox']) != scenario['sandbox']:
                raise ValueError('Event damage comes from another sandbox')
            t = number(event['time'], 'time')
            body = number(event['body'], 'body damage')
            crit = number(event.get('crit', body), 'crit damage')
            hit = number(event.get('hit_probability', 1), 'hit probability', maximum=1)
            precision = number(event.get('crit_given_hit', 0), 'crit probability', maximum=1)
            multiplier = 1
            if event.get('effect_ids'):
                if event.get('component') != 'weapon' or event.get('conditions_satisfied') is not True:
                    raise ValueError('Effects require weapon component and explicitly satisfied conditions')
                multiplier = effect_multiplier(event['effect_ids'], scenario['mode'], scenario['sandbox'],
                    scenario.get('allow_partial', False))['multiplier']
            damage = hit*(precision*crit + (1-precision)*body)*multiplier
            number(damage, 'expected damage')
            timeline.append((t, damage))
        row = {'name': build['name'], 'windows': [], 'event_count': len(events),
               'conditions': build.get('conditions', []), 'utility': build.get('utility', [])}
        for t in windows:
            damage = math.fsum(d for time, d in timeline if time < t)
            row['windows'].append({'seconds': t, 'expected_damage': damage, 'dps': damage/t})
        if 'survival' in build:
            row['survival'] = survival(build['survival']['hp'], build['survival']['independent_dr'])
        output.append(row)
    return {'sandbox': scenario['sandbox'], 'mode': scenario['mode'], 'target': scenario['target'],
            'damage_baseline': scenario['damage_baseline'], 'provenance': scenario['provenance'],
            'baseline_sandbox': scenario['baseline_sandbox'], 'baseline_kind': scenario['baseline_kind'],
            'interval_convention': '[0,T); t is hit time, not trigger time',
            'allow_partial': scenario.get('allow_partial', False), 'builds': output,
            'limitations': 'Baseline metadata are caller declarations, not independent source validation. Only supplied events/resources/conditions are evaluated. No legal-roll or ability-loop solver.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('scenario', type=Path)
    p.add_argument('--out', type=Path)
    a = p.parse_args()
    try:
        result = evaluate(json.loads(a.scenario.read_text(encoding='utf-8-sig')))
        value = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
        if a.out:
            a.out.write_text(value, encoding='utf-8')
        else:
            print(value)
    except (ValueError, KeyError) as exc:
        p.exit(1, str(exc)+'\n')


if __name__ == '__main__':
    main()
