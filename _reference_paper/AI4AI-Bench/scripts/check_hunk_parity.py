#!/usr/bin/env python3
"""Flag English section/table files that changed without their Chinese mirror changing.

check_mirror.py compares per-file counts of five token kinds (num/label/ref/cite/tt).
That catches drifting numbers and keys, but it is blind to three classes of change,
all three of which actually slipped through in v5.0:

  1. numerals spelled as words   ("twenty points" -> "sixteen points": no num token)
  2. pure prose edits            (a caption gaining a scope qualifier)
  3. same-count relocations      (moving \texttt{formal_state} from body into a footnote)

This script works on the git diff instead of the file contents: for every EN file with
uncommitted changes it asks whether the paired ZH file also changed. A pair where EN
moved and ZH did not is the failure mode above. It cannot prove a ZH edit says the same
thing as its EN counterpart -- only a human can -- but it can prove no one forgot to look.

Usage:
    python3 scripts/check_hunk_parity.py              # working tree vs HEAD
    python3 scripts/check_hunk_parity.py <ref>        # working tree vs <ref>

Exit status: 0 = every changed EN file has a changed ZH counterpart, 1 = otherwise.
"""
import os
import re
import subprocess
import sys

ROOT = os.environ.get('PAPER_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PAIRS = [('Sections', 'Sections_zh'), ('Tables', 'Tables_zh')]


def git(*args):
    r = subprocess.run(
        ['git', '-C', ROOT] + list(args),
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if r.returncode:
        sys.exit(f"git {' '.join(args)} failed:\n{r.stderr}")
    return r.stdout


def hunks(path, ref):
    """Number of @@ hunks in the diff for one path (0 if unchanged/absent)."""
    out = git('diff', '-U0', ref, '--', path)
    return len(re.findall(r'^@@ ', out, re.M))


def main():
    ref = sys.argv[1] if len(sys.argv) > 1 else 'HEAD'
    rows, missing, unpaired = [], [], []

    for en_dir, zh_dir in PAIRS:
        en_abs = os.path.join(ROOT, en_dir)
        if not os.path.isdir(en_abs):
            continue
        for name in sorted(os.listdir(en_abs)):
            if not name.endswith('.tex'):
                continue
            en_rel = f"{en_dir}/{name}"
            zh_rel = f"{zh_dir}/{name}"
            if not os.path.exists(os.path.join(ROOT, zh_rel)):
                unpaired.append(en_rel)
                continue
            en_h, zh_h = hunks(en_rel, ref), hunks(zh_rel, ref)
            if en_h or zh_h:
                rows.append((en_rel, en_h, zh_h))
                if en_h and not zh_h:
                    missing.append((en_rel, zh_rel, en_h))

    if rows:
        w = max(len(r[0]) for r in rows)
        print(f"{'file':<{w}}  {'EN':>3}  {'ZH':>3}   verdict")
        print('-' * (w + 22))
        for rel, en_h, zh_h in rows:
            if en_h and not zh_h:
                verdict = 'ZH NOT TOUCHED'
            elif zh_h and not en_h:
                verdict = 'ZH-only edit'
            else:
                verdict = 'both moved'
            print(f"{rel:<{w}}  {en_h:>3}  {zh_h:>3}   {verdict}")
    else:
        print(f"no changes in either tree against {ref}")

    if unpaired:
        print(f"\nEN files with no ZH counterpart: {', '.join(unpaired)}")

    print()
    if missing:
        print(f"FAIL: {len(missing)} EN file(s) changed while the ZH mirror did not:")
        for en_rel, zh_rel, en_h in missing:
            print(f"  {en_rel} ({en_h} hunk(s)) -> {zh_rel} unchanged")
            print(f"      review with: git -C {ROOT} diff {ref} -- {en_rel}")
        return 1

    print("PARITY OK: every changed EN file has a changed ZH counterpart.")
    print("Note: this proves both sides moved, not that they now say the same thing.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
