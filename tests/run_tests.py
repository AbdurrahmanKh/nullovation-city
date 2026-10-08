"""Builds the tool, runs the test passes in order, and prints one line per pass.

    python3 tests/run_tests.py                   build, then every pass
    python3 tests/run_tests.py test9 test16      build, then just these passes (by number, or the full name)
    python3 tests/run_tests.py --no-build ...    skip the build

Each pass's full output goes to tests/data/logs/<pass>.log. The exit code is 0 only when every pass ran to its end
with no FAIL line and no console errors. On Windows, use `python` in place of `python3`."""
import os, pathlib, re, subprocess, sys, time

TESTS = pathlib.Path(__file__).resolve().parent
ROOT = TESTS.parent                                              # the source folder
PASSES = ['test02_map', 'test04_seed_data', 'test05_bubble_art', 'test06_generics', 'test07_project_view',
          'test08_bubble_tasks', 'test09_urgency', 'test10_sidebar', 'test11_load_plan', 'test12_folder_links',
          'test13_traffic', 'test14_data_file', 'test15_notes_milestones', 'test16_dropups', 'test17_source',
          'test18_open_in_claude', 'test19_street_props', 'test20_settings', 'test21_city_settings', 'test22_edit_city']
ENV = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')    # Arabic text reads and prints on Windows too


def run(args, timeout=None):
    return subprocess.run([sys.executable, *args], cwd=ROOT, env=ENV, capture_output=True, text=True,
                          encoding='utf-8', errors='replace', timeout=timeout)


def find(arg):
    """A pass by its full name or its number: test09_urgency, test09, test9 and 9 all name the same pass."""
    m = re.fullmatch(r'(?:test)?0*(\d+)(?:_\w*)?(?:\.py)?', arg)
    hits = [p for p in PASSES if p == arg or (m and int(p[4:6]) == int(m.group(1)))]
    return hits[0] if len(hits) == 1 else None


def main(argv):
    asked = [a for a in argv if a != '--no-build']
    unknown = [a for a in asked if not find(a)]
    if unknown:
        sys.exit('Unknown pass: ' + ', '.join(unknown) + '. The passes are: ' + ' '.join(PASSES))
    chosen = [find(a) for a in asked] or PASSES
    if '--no-build' not in argv:
        r = run(['build.py'])
        print((r.stdout + r.stderr).strip())
        if r.returncode:
            sys.exit(1)
    logs = TESTS / 'data' / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    passed = failed = 0
    problems = []
    for t in chosen:
        start = time.time()
        try:
            r = run(['tests/' + t + '.py'], timeout=900)
            out, stopped = r.stdout + r.stderr, r.returncode != 0
        except subprocess.TimeoutExpired as e:
            out, stopped = (e.stdout or '') + (e.stderr or '') + '\nstopped after 900 s', True
        (logs / (t + '.log')).write_text(out, encoding='utf-8')
        lines = out.splitlines()
        p, f = sum(l.startswith('PASS') for l in lines), sum(l.startswith('FAIL') for l in lines)
        console = not stopped and 'no console errors' not in out
        passed, failed = passed + p, failed + f
        note = ', stopped with an error' if stopped else ', console errors' if console else ''
        print(f'{t}: {p} pass, {f} fail{note} ({time.time() - start:.0f} s)')
        for l in lines:
            if l.startswith('FAIL'):
                print('  ' + l)
        if stopped:
            for l in [l for l in lines if l.strip()][-3:]:
                print('  | ' + l)
        if f or stopped or console:
            problems.append(t)
    print(f'{len(chosen)} passes, {passed} checks passed, {failed} failed'
          + ('. Look at: ' + ' '.join(problems) + ' (logs in tests/data/logs)' if problems else ''))
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main(sys.argv[1:])
