from dataclasses import replace
import unittest
import experiment as e

class PolicyTests(unittest.TestCase):
    def row(self, name, method='action_flow'):
        s = next(s for s in e.named_scenarios() if s.name == name)
        return e.run_one(s, method)

    def test_declared_fixture_oracle(self):
        run = e.build_run()
        self.assertEqual(run['expectation_mismatches'], [])
        self.assertEqual(len(run['named']), 36)

    def test_main_type_is_not_commit(self):
        row = self.row('same_origin_untrusted')
        self.assertTrue(row['type_allowed'])
        self.assertFalse(row['save_allowed'])
        self.assertEqual(row['buffer'], e.VALUE)
        self.assertIsNone(row['committed'])
        self.assertEqual(row['captures'], [])
        for m in ('origin_only', 'flow_only'):
            other = self.row('same_origin_untrusted', m)
            self.assertEqual(other['committed'], e.VALUE)
            self.assertEqual(other['captures'], [{'stage': 'save', 'value': e.VALUE}])

    def test_benign_twins_and_declassification(self):
        self.assertEqual(self.row('trusted_same_origin')['committed'], e.VALUE)
        self.assertEqual(self.row('trusted_public_cross')['committed'], 'invented-product')
        self.assertIsNone(self.row('trusted_public_cross', 'origin_only')['committed'])
        self.assertEqual(self.row('trusted_declassification_cross')['committed'], e.VALUE)
        self.assertIsNone(self.row('trusted_declassification_cross', 'flow_only')['committed'])

    def test_argument_integrity_is_checked(self):
        self.assertFalse(self.row('untrusted_argument_same')['save_allowed'])
        self.assertTrue(self.row('untrusted_argument_same')['type_allowed'])

    def test_both_reader_sets_are_checked(self):
        for name in ('untrusted_private_cross', 'context_restricts_cross', 'user_only_secret_untrusted_same'):
            row = self.row(name)
            self.assertFalse(row['type_allowed'])
            self.assertIsNone(row['buffer'])
            self.assertIsNone(row['save_allowed'])
            self.assertEqual(row['captures'], [])

    def test_no_save_no_commit(self):
        for m in e.METHODS:
            row = self.row('no_save', m)
            self.assertEqual(row['buffer'], e.VALUE)
            self.assertIsNone(row['committed'])
            self.assertIsNone(row['save_allowed'])

    def test_auto_submit_not_reversed_by_later_hold(self):
        row = self.row('auto_submit_untrusted_same')
        self.assertFalse(row['save_allowed'])
        self.assertEqual(row['committed'], e.VALUE)
        self.assertEqual(row['captures'], [{'stage': 'type_auto_submit', 'value': e.VALUE}])
        self.assertEqual([c['stage'] for c in self.row('auto_submit_untrusted_same', 'origin_only')['captures']], ['type_auto_submit', 'save'])

    def test_bad_label_is_visible_limitation(self):
        row = self.row('false_trusted_label')
        self.assertFalse(row['input']['label_is_correct'])
        self.assertTrue(row['save_allowed'])
        self.assertEqual(row['committed'], e.VALUE)

    def test_finite_truth_table_independent_oracle(self):
        # Table keyed by (context trusted, argument trusted, reader allowed).
        # Each entry is (type, save-if-buffered); authored independent of policy.
        action = {'000': (False, None), '001': (True, False),
                  '010': (False, None), '011': (True, False),
                  '100': (False, None), '101': (True, False),
                  '110': (True, True), '111': (True, True)}
        states = list(e.matrix_scenarios())
        self.assertEqual(len(states), 32)
        self.assertEqual(len({s.name for s in states}), 32)
        for s in states:
            cross, ctx, arg, reader, auto = s.name.removeprefix('matrix_')
            expected = {'origin_only': (cross == '0', True if cross == '0' else None),
                        'flow_only': (reader == '1', True if reader == '1' else None),
                        'action_flow': action[ctx + arg + reader]}
            for m, (typed, saved) in expected.items():
                with self.subTest(state=s.name, method=m):
                    r = e.run_one(s, m)
                    self.assertEqual((r['type_allowed'], r['save_allowed']), (typed, saved))
                    stages = ([] if not typed else (['type_auto_submit'] if auto == '1' else []) + (['save'] if saved else []))
                    self.assertEqual([c['stage'] for c in r['captures']], stages)
                    self.assertEqual(r['committed'], e.VALUE if stages else None)
                    self.assertEqual(r['buffer'], e.VALUE if typed else None)

    def test_exact_bytes_immutable_inputs_and_determinism(self):
        s = replace(e.named_scenarios()[1], value='literal\nfixture Ω')
        before = repr(s)
        for m in e.METHODS:
            row = e.run_one(s, m)
            self.assertEqual(row['committed'], s.value)
            self.assertEqual(repr(s), before)
        self.assertEqual(e.build_run(), e.build_run())

    def test_unknown_method_action_rejected(self):
        s = e.named_scenarios()[0]
        for method, action in [('other', 'type'), ('action_flow', 'execute')]:
            with self.assertRaises(ValueError):
                e.decide(s, method, action)

if __name__ == '__main__':
    unittest.main()
