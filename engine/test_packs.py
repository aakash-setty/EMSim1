#!/usr/bin/env python3
"""Run every check for one pack, or for every pack, one pack at a time.

    python3 engine/test_packs.py              every pack
    python3 engine/test_packs.py DKA TSS      named packs
    python3 engine/test_packs.py --quick DKA  engine tests and scenarios only

For each pack it builds a one-pack simulator into a scratch folder (so build/ is not
touched and the file holds only that case), then runs the engine tests, the scenario
runner, the validator, the validator's negative tests and the deterioration timeline, and
prints one line per pack. Exit status is non-zero if anything failed.

Why one pack at a time: `engine/engine-tests.js` checks every case in the file it is
given. Against build/simulator.html, which holds every case, each pack's run re-checks
every other pack, so the whole suite grows with the square of the number of cases (about
18 s at seven cases, about 13 minutes at a hundred). Against a one-pack build each run is
constant, and the library can grow.

The full local build (`python3 engine/build_simulator.py`) is still what the site, the
private packs and a browser play-through come from. This runner does not replace it.
"""
import os, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from paths import CasePack, list_packs   # noqa: E402


def run(cmd, env=None, cwd=ROOT):
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)


def last_line(out, needle=None):
    lines = [l for l in out.strip().splitlines() if l.strip()]
    if needle:
        hits = [l for l in lines if needle in l]
        if hits:
            return hits[-1].strip()
    return lines[-1].strip() if lines else ""


def test_pack(prefix, quick):
    pk = CasePack(prefix)
    scratch = tempfile.mkdtemp(prefix="emsim-" + prefix + "-")
    env = dict(os.environ, EMSIM_BUILD_DIR=scratch)
    results, failed = [], False
    t0 = time.time()
    try:
        rc, out = run([sys.executable, os.path.join(HERE, "build_simulator.py"), prefix], env=env)
        if rc != 0:
            return prefix, True, [f"build failed: {last_line(out)}"], time.time() - t0
        sim = os.path.join(scratch, "simulator.html")

        rc, out = run(["node", os.path.join(HERE, "engine-tests.js"), sim, pk.tests, prefix])
        results.append("engine " + last_line(out, "checks"))
        failed |= rc != 0

        rc, out = run([sys.executable, os.path.join(HERE, "sim_runner.py"), pk.dir])
        results.append("scenarios " + last_line(out, "scenarios"))
        failed |= rc != 0

        if not quick:
            rc, out = run([sys.executable, os.path.join(HERE, "validate_case.py"), pk.dir])
            results.append("validator " + last_line(out, "errors"))
            failed |= rc != 0

            rc, out = run([sys.executable, os.path.join(HERE, "validator-tests.py"), pk.dir])
            results.append("validator-tests " + last_line(out, "checks"))
            failed |= rc != 0

            rc, out = run([sys.executable, os.path.join(HERE, "deterioration_timeline.py"), pk.dir])
            results.append("timeline " + ("written" if rc == 0 else "FAILED: " + last_line(out)))
            failed |= rc != 0
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    return prefix, failed, results, time.time() - t0


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    quick = "--quick" in sys.argv
    packs = args or list_packs()
    bad = 0
    t0 = time.time()
    for prefix in packs:
        name, failed, results, secs = test_pack(prefix, quick)
        bad += failed
        print(f"{'FAIL' if failed else 'ok  '} {name:<7} {secs:5.1f}s  " + " | ".join(results))
    print(f"\n{len(packs)} packs, {bad} failed, {time.time() - t0:.1f}s")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
