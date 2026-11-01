"""Shared validation and JSON transport for bounded offline models."""
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def default_review_state():
    config=ROOT/'assets/private/monitor-config.json'
    if config.exists():return Path(load(config)['review_state'])
    return ROOT/'assets/private/review-state.json'


def finite(x, label, low=0, high=None):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError(f'{label}: finite number required')
    if x < low or (high is not None and x > high):
        raise ValueError(f'{label}: outside [{low}, {high}]')
    return x


def integer(x, label, low=0, high=100000):
    finite(x, label, low, high)
    if not isinstance(x, int):
        raise ValueError(f'{label}: integer required')
    return x


def unique(rows, label):
    result = {}
    for r in rows:
        key = r.get('id')
        if not isinstance(key, str) or not key or key in result:
            raise ValueError(f'{label}: nonempty unique id required')
        result[key] = r
    return result


def load(path):
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ValueError('Duplicate JSON key: ' + k)
            result[k] = v
        return result
    def invalid(x):
        raise ValueError('Nonfinite JSON literal: ' + x)
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),
                      object_pairs_hook=pairs, parse_constant=invalid)


def emit(data, path=None):
    value = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)
    if path:
        Path(path).write_text(value+'\n', encoding='utf-8')
    else:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        print(value)


def cli_error(parser, fn):
    try:
        return fn()
    except (ValueError, KeyError, OSError, TypeError, IndexError) as exc:
        parser.exit(2, str(exc)+'\n')
