"""
Golden-file test runner -- provided, do not modify.

Runs main.py once per (test program, output mode) and compares the file
it writes against tests/<name>.<mode>.expected.txt. Only modes that HAVE
an expected file are checked, so a test with no .3ac.expected.txt simply
isn't checked for 3AC.

Usage:
    python run_tests.py                 # every tests/*.tc
    python run_tests.py test10 test13   # just these programs
    python run_tests.py -v test13       # also print a diff for each failure
    python run_tests.py -spim           # ALSO run each .s on SPIM and check what it prints
                                        # (needs the command-line `spim`, e.g. on Linux/WSL:
                                        #  sudo apt install spim)

Works the same on Windows, Linux and macOS (no `diff` command needed).
It also checks once that the grammar builds WITHOUT conflict warnings.
"""
import difflib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.join(HERE, "tests")

# (main.py flag, extension main.py writes, golden-file key)
MODES = [
    ("-tokens", ".toks", "toks"),
    ("-ast", ".ast", "ast"),
    ("-symtab", ".sym", "sym"),
    ("-check", ".check", "check"),
    ("-3ac", ".3ac", "3ac"),
    ("-compile", ".spim", "s"),
]


def normalize(text):
    return [line.rstrip() for line in text.replace("\r\n", "\n").strip("\n").split("\n")]


def run_one(tc_path, flag, ext):
    subprocess.run([sys.executable, os.path.join(HERE, "main.py"), flag, tc_path],
                   cwd=HERE, capture_output=True, text=True)
    out_path = tc_path + ext
    if not os.path.exists(out_path):
        return None
    with open(out_path) as f:
        return f.read()


def grammar_conflicts():
    """
    WEEK 8: builds the parser in a fresh process and returns SLY's conflict
    warnings (empty list = conflict-free grammar). Golden files alone can't
    catch an unresolved dangling else: SLY's silent default (shift) happens to
    produce the right AST, so the grammar itself is checked separately.
    """
    r = subprocess.run([sys.executable, "-c", "import tinycstr_parser"],
                       cwd=HERE, capture_output=True, text=True)
    return [line for line in (r.stdout + r.stderr).splitlines() if "conflict" in line]


def spim_output(asm_path):
    """
    WEEK 9: runs a generated .s on the command-line `spim` and returns what
    the PROGRAM printed (SPIM's own banner, up to its "Loaded:" line, is
    dropped). Returns None if `spim` isn't installed.
    """
    try:
        r = subprocess.run(["spim", "-file", asm_path], capture_output=True, text=True,
                           timeout=20)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    lines = r.stdout.replace("\r\n", "\n").split("\n")
    for i, line in enumerate(lines):
        if line.startswith("Loaded:"):
            lines = lines[i + 1:]
            break
    return "\n".join(lines)


def main(argv):
    verbose = "-v" in argv
    use_spim = "-spim" in argv
    names = [a for a in argv if a not in ("-v", "-spim")]
    if not names:
        names = sorted(f[:-3] for f in os.listdir(TESTS) if f.endswith(".tc"))

    passed = failed = 0
    conflicts = grammar_conflicts()
    if conflicts:
        failed += 1
        print("FAIL  grammar          " + " / ".join(c.strip() for c in conflicts))
        print("      (see docs/sly_help3.md #3-#4)")
    else:
        passed += 1
        print("PASS  grammar          no shift/reduce or reduce/reduce conflicts")
    for name in names:
        tc_path = os.path.join(TESTS, name + ".tc")
        if not os.path.exists(tc_path):
            print(f"?? {name}: no such test program")
            failed += 1
            continue
        results = []
        for flag, ext, key in MODES:
            golden = os.path.join(TESTS, f"{name}.{key}.expected.txt")
            if not os.path.exists(golden):
                continue
            with open(golden) as f:
                expected = normalize(f.read())
            actual_text = run_one(tc_path, flag, ext)
            actual = normalize(actual_text) if actual_text is not None else ["<no output file>"]
            ok = actual == expected
            results.append((key, ok))
            if ok:
                passed += 1
            else:
                failed += 1
                if verbose:
                    print(f"--- {name}.{key}: expected vs. yours")
                    for line in difflib.unified_diff(expected, actual, "expected", "yours",
                                                     lineterm=""):
                        print("    " + line)
        golden = os.path.join(TESTS, f"{name}.spim_output.expected.txt")
        if use_spim and os.path.exists(golden):
            if not os.path.exists(tc_path + ".spim"):
                run_one(tc_path, "-compile", ".spim")
            got = spim_output(tc_path + ".spim")
            if got is None:
                print("??  `spim` command not found -- install it, or drop -spim")
                return 1
            with open(golden) as f:
                ok = normalize(got) == normalize(f.read())
            results.append(("run-on-spim", ok))
            passed, failed = passed + ok, failed + (not ok)
            if not ok and verbose:
                print(f"--- {name} on SPIM printed: {got.strip()!r}")
        summary = "  ".join(f"{key}:{'ok' if ok else 'FAIL'}" for key, ok in results)
        status = "PASS" if all(ok for _, ok in results) else "FAIL"
        print(f"{status}  {name:<16} {summary}")

    print(f"\n{passed} checks passed, {failed} failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
