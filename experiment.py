"""Independent synthetic origin/action-policy assay. No browser or network."""
from dataclasses import dataclass, asdict, replace
from itertools import product
from pathlib import Path
import hashlib
import json

A = 'site-a.invalid'
B = 'site-b.invalid'
PUBLIC = frozenset(('user', A, B))  # finite reader universe, not the real Web
METHODS = ('origin_only', 'flow_only', 'action_flow')
VALUE = 'invented-recovery@example.invalid'

@dataclass(frozen=True)
class Label:
    trusted: bool
    readers: frozenset[str]
    origins: frozenset[str] = frozenset((A,))

@dataclass(frozen=True)
class Scenario:
    name: str
    context: Label
    argument: Label
    target: str = A
    auto_submit: bool = False
    request_save: bool = True
    label_is_correct: bool = True
    value: str = VALUE


def trusted_action(s):
    return s.context.trusted and s.argument.trusted


def permitted_flow(s):
    return s.target in s.context.readers and s.target in s.argument.readers


def decide(s, method, action):
    if method not in METHODS or action not in ('type', 'save'):
        raise ValueError('unknown method/action')
    if method == 'origin_only':
        return (s.context.origins | s.argument.origins) <= {s.target}
    if method == 'flow_only':
        return permitted_flow(s)
    trusted = trusted_action(s)
    permitted = permitted_flow(s)
    if action == 'type':
        return trusted or permitted
    return trusted  # consequential Save, target is a trusted origin


def record_label(label):
    return {'trusted': label.trusted, 'readers': sorted(label.readers),
            'origins': sorted(label.origins)}


def run_one(s, method):
    buffer = None
    committed = None
    events = []
    captures = []
    type_allowed = decide(s, method, 'type')
    events.append({'action': 'type', 'allowed': type_allowed})
    if type_allowed:
        buffer = s.value
        if s.auto_submit:
            committed = buffer
            captures.append({'stage': 'type_auto_submit', 'value': committed})
    save_allowed = None
    if s.request_save and buffer is not None:
        save_allowed = decide(s, method, 'save')
        events.append({'action': 'save', 'allowed': save_allowed})
        if save_allowed:
            committed = buffer
            captures.append({'stage': 'save', 'value': committed})
    elif s.request_save:
        events.append({'action': 'save', 'allowed': None, 'reason': 'type_held'})
    else:
        events.append({'action': 'save', 'allowed': None, 'reason': 'not_requested'})
    return {
        'scenario': s.name, 'method': method,
        'input': {'context': record_label(s.context), 'argument': record_label(s.argument),
                  'target': s.target, 'value': s.value, 'auto_submit': s.auto_submit,
                  'request_save': s.request_save, 'label_is_correct': s.label_is_correct},
        'predicates': {'trusted_action': trusted_action(s), 'permitted_flow': permitted_flow(s)},
        'type_allowed': type_allowed, 'save_allowed': save_allowed,
        'buffer': buffer, 'committed': committed, 'events': events, 'captures': captures,
    }


def named_scenarios():
    trusted = Label(True, PUBLIC)
    untrusted = Label(False, PUBLIC)
    secret = Label(True, frozenset(('user', A)))
    base = Scenario('same_origin_untrusted', untrusted, secret)
    return [
        base,
        replace(base, name='trusted_same_origin', context=trusted),
        Scenario('trusted_public_cross', trusted, trusted, target=B, value='invented-product'),
        replace(base, name='untrusted_private_cross', target=B),
        replace(base, name='untrusted_public_cross', argument=trusted, target=B),
        Scenario('untrusted_argument_same', trusted, replace(secret, trusted=False)),
        Scenario('trusted_declassification_cross', trusted, secret, target=B),
        replace(base, name='user_only_secret_untrusted_same', argument=Label(True, frozenset(('user',)))),
        replace(base, name='no_save', request_save=False),
        replace(base, name='false_trusted_label', context=trusted, label_is_correct=False),
        replace(base, name='auto_submit_untrusted_same', auto_submit=True),
        Scenario('context_restricts_cross', Label(False, frozenset(('user', A))), trusted, target=B),
    ]

# Declarative expected (type admitted, Save admitted or not attempted, any commit).
# These are deliberately independent of decide(), not computed from its predicates.
EXPECTED = {
    'same_origin_untrusted': [(True, True, True), (True, True, True), (True, False, False)],
    'trusted_same_origin': [(True, True, True)] * 3,
    'trusted_public_cross': [(False, None, False), (True, True, True), (True, True, True)],
    'untrusted_private_cross': [(False, None, False)] * 3,
    'untrusted_public_cross': [(False, None, False), (True, True, True), (True, False, False)],
    'untrusted_argument_same': [(True, True, True), (True, True, True), (True, False, False)],
    'trusted_declassification_cross': [(False, None, False), (False, None, False), (True, True, True)],
    'user_only_secret_untrusted_same': [(True, True, True), (False, None, False), (False, None, False)],
    'no_save': [(True, None, False)] * 3,
    'false_trusted_label': [(True, True, True)] * 3,
    'auto_submit_untrusted_same': [(True, True, True), (True, True, True), (True, False, True)],
    'context_restricts_cross': [(False, None, False)] * 3,
}


def matrix_scenarios():
    # Independent predicate combinations, not claimed reachable browser histories.
    for cross, ctx, arg, reader, auto in product((False, True), repeat=5):
        target = B if cross else A
        readers = PUBLIC if reader else frozenset(('user',))
        bits = ''.join(str(int(x)) for x in (cross, ctx, arg, reader, auto))
        yield Scenario('matrix_' + bits, Label(ctx, PUBLIC), Label(arg, readers), target, auto)


def signature(row):
    return (row['type_allowed'], row['save_allowed'], row['committed'] is not None)


def build_run():
    rows = [run_one(s, m) for s in named_scenarios() for m in METHODS]
    mismatches = []
    for row in rows:
        expectation = EXPECTED[row['scenario']][METHODS.index(row['method'])]
        row['expected'] = dict(zip(('type_allowed', 'save_allowed', 'any_commit'), expectation))
        if signature(row) != expectation:
            mismatches.append([row['scenario'], row['method']])
    matrix = [run_one(s, m) for s in matrix_scenarios() for m in METHODS]
    return {
        'schema': 1, 'scope': 'synthetic fixed policy predicates and in-memory action effects',
        'no_model_browser_network': True,
        'matrix_scope': '32 independent predicate/effect combinations, not sampled or necessarily reachable browser states',
        'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'named_fixture_count': 12, 'named_row_count': len(rows),
        'matrix_state_count': 32, 'matrix_row_count': len(matrix),
        'expectation_mismatches': mismatches, 'named': rows, 'matrix': matrix,
    }


def evidence(run):
    lines = ['# Exact synthetic action traces', '',
        'No model, browser or network ran. Type and Save decisions concern the declared local policy model.',
        'A capture is an in-memory state change. No real profile is published.', '',
        '| Fixture | Method | Type | Save | Buffered | Capture stages |',
        '|---|---|---|---|---|---|']
    for r in run['named']:
        show = lambda v: 'not attempted' if v is None else ('allow' if v else 'hold')
        stages = ', '.join(c['stage'] for c in r['captures']) or 'none'
        lines.append(f"|{r['scenario']}|{r['method']}|{show(r['type_allowed'])}|{show(r['save_allowed'])}|{'yes' if r['buffer'] is not None else 'no'}|{stages}|")
    lines += ['', 'Denominator:12 named fixtures ×3 methods =36 rows;32 additional independent predicate/effect states ×3 methods =96 rows in run.json.',
        'No population attack rate or uncertainty is inferred from either set.', '',
        'The main same_origin_untrusted trace buffers identical invented bytes in all methods. Origin only and Flow only commit at Save. Action flow holds Save and keeps the buffer.',
        'trusted_public_cross commits under both label methods but is held by Origin only. trusted_declassification_cross commits under Action flow because trusted actions may declassify in this source-inspired model.',
        'auto_submit_untrusted_same captures at type time under every method, even when Action flow later holds Save. Holding a later action does not undo an earlier side effect.',
        'false_trusted_label passes every method: the policy does not validate the truth of assigned labels.', '']
    return '\n'.join(lines)


def main():
    result = build_run()
    if result['expectation_mismatches']:
        raise SystemExit('fixture expectations failed: ' + repr(result['expectation_mismatches']))
    root = Path(__file__).parent / 'artifacts'
    root.mkdir(exist_ok=True)
    (root / 'run.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    (root / 'evidence.md').write_text(evidence(result))
    print(json.dumps({k: result[k] for k in ('named_row_count', 'matrix_row_count', 'expectation_mismatches')}))

if __name__ == '__main__':
    main()
