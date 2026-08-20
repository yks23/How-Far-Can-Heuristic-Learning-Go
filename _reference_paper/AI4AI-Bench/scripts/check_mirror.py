#!/usr/bin/env python3
"""Verify the ZH mirror preserves every number, label, ref, cite key and texttt token."""
import re, sys, os
from collections import Counter

def _find_root():
    """Locate the paper root whether run from it, from scripts/, or elsewhere."""
    env = os.environ.get('PAPER_ROOT')
    if env:
        return env
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (os.getcwd(), here, os.path.dirname(here)):
        if os.path.isdir(os.path.join(cand, 'Sections')):
            return cand
    return '/tmp/ai4ai-paper'       # local scratch copy, last resort


ROOT = _find_root()
EN_S, ZH_S = os.path.join(ROOT, "Sections"), os.path.join(ROOT, "Sections_zh")
EN_T, ZH_T = os.path.join(ROOT, "Tables"),   os.path.join(ROOT, "Tables_zh")

# A number token: integers/decimals, optionally with % or thousands comma ({,})
NUM = re.compile(r'(?<![A-Za-z0-9_.])(\d+(?:\{,\}\d+)?(?:\.\d+)?)')
LABEL = re.compile(r'\\label\{([^}]*)\}')
REF   = re.compile(r'\\(?:ref|autoref)\{([^}]*)\}')
CITE  = re.compile(r'\\cite[a-z]*\{([^}]*)\}')
TT    = re.compile(r'\\texttt\{([^}]*)\}')

def toks(path):
    s = open(path, encoding='utf-8').read()
    # strip LaTeX comments so provenance notes don't count
    s = re.sub(r'(?<!\\)%.*', '', s)
    cites = []
    for m in CITE.finditer(s):
        cites += [k.strip() for k in m.group(1).split(',')]
    return {
        'num':   Counter(NUM.findall(s)),
        'label': Counter(LABEL.findall(s)),
        'ref':   Counter(REF.findall(s)),
        'cite':  Counter(cites),
        'tt':    Counter(TT.findall(s)),
    }

# Numerals English spells out as words but Chinese writes as digits. Each entry is
# (file, kind, token, count, the English phrase that justifies it). Verified by grep.
WHITELIST = {
    ('8_conclusion.tex', 'num', '27'): (1, 'EN "Twenty-seven receipts are"'),
    ('4_results.tex',    'num', '18'): (1, 'EN "Fourteen of eighteen improve on the start"'),
    ('4_results.tex',    'num', '14'): (1, 'EN "Fourteen of eighteen improve on the start"'),
}

def cmp_pair(en_path, zh_path, kinds):
    if not os.path.exists(zh_path):
        print(f"  !! MISSING {zh_path}")
        return 1
    a, b = toks(en_path), toks(zh_path)
    base = os.path.basename(en_path)
    bad = 0
    for k in kinds:
        only_en, only_zh = a[k] - b[k], b[k] - a[k]
        for tok in list(only_zh):
            allow = WHITELIST.get((base, k, tok))
            if allow and only_zh[tok] <= allow[0]:
                print(f"  [{k}] ZH-only {tok!r} x{only_zh[tok]} allowed: {allow[1]}")
                del only_zh[tok]
        if only_en or only_zh:
            bad = 1
            print(f"  [{k}] EN-only: {dict(only_en)}")
            print(f"  [{k}] ZH-only: {dict(only_zh)}")
    return bad

kinds = sys.argv[1:] or ['num', 'label', 'ref', 'cite', 'tt']
fails = 0
for en_dir, zh_dir in ((EN_S, ZH_S), (EN_T, ZH_T)):
    for f in sorted(os.listdir(en_dir)):
        if not f.endswith('.tex'):
            continue
        r = cmp_pair(os.path.join(en_dir, f), os.path.join(zh_dir, f), kinds)
        print(("FAIL " if r else "ok   ") + os.path.join(os.path.basename(zh_dir), f))
        fails += r
print(f"\n{'ALL MATCH' if not fails else str(fails) + ' file(s) with differences'}")
