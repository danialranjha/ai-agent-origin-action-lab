"""Run focused tests and verify two meaningful faulty policies fail assertions."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile

DRIVER = '''import io,json,unittest
s=unittest.defaultTestLoader.loadTestsFromName('test_experiment')
r=unittest.TextTestRunner(stream=io.StringIO()).run(s)
print(json.dumps({'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skipped':len(r.skipped),'successful':r.wasSuccessful()}))
'''

def suite(root):
    p = subprocess.run([sys.executable, '-B', '-c', DRIVER], cwd=root, text=True, capture_output=True, timeout=30)
    if p.returncode != 0:
        raise RuntimeError('test runner process failed: ' + p.stderr)
    return json.loads(p.stdout)

def main():
    root = Path(__file__).resolve().parent
    normal = suite(root)
    if not normal['successful'] or normal['skipped']:
        raise SystemExit('normal suite failed: ' + repr(normal))
    original = (root / 'experiment.py').read_text()
    mutations = {}
    changes = {
        'omit_save_integrity': ('return trusted  # consequential Save, target is a trusted origin', 'return permitted  # intentional faulty Save policy'),
        'overrestrict_typing': ('return trusted or permitted', 'return trusted and permitted'),
    }
    for name, (old, new) in changes.items():
        assert original.count(old) == 1
        with tempfile.TemporaryDirectory(prefix='origin-action-check-') as temp:
            target = Path(temp)
            shutil.copyfile(root / 'test_experiment.py', target / 'test_experiment.py')
            (target / 'experiment.py').write_text(original.replace(old, new))
            result = suite(target)
            if result['failures'] == 0 or result['errors'] or result['skipped']:
                raise SystemExit('mutation not caught by assertions: ' + name + repr(result))
            mutations[name] = result
    result = {'normal': normal, 'mutations': mutations, 'scope': 'fixed fixtures and finite predicate matrix, no live agent efficacy'}
    (root / 'artifacts').mkdir(exist_ok=True)
    (root / 'artifacts' / 'checks.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result))

if __name__ == '__main__':
    main()
