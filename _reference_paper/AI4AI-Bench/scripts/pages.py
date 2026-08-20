#!/usr/bin/env python3
"""Where does the main text end? Reads the built PDF rather than guessing.

Main text is everything before the appendix. The .aux carries the page number
of every \\label, so the first appendix label's page is the boundary.
"""
import re
import subprocess
import sys

JOB = sys.argv[1] if len(sys.argv) > 1 else 'paper'
aux = open(f'{JOB}.aux', errors='ignore').read()

# \newlabel{name}{{printed}{page}...}
pages = {}
for m in re.finditer(r'\\newlabel\{([^}]+)\}\{\{([^}]*)\}\{(\d+)\}', aux):
    pages[m.group(1)] = (m.group(2), int(m.group(3)))

total = None
log = open(f'{JOB}.log', errors='ignore').read()
mm = re.search(r'Output written on \S+ \((\d+) pages', log)
if mm:
    total = int(mm.group(1))

app = [(n, p) for n, (_, p) in pages.items() if n.startswith('app:')]
first_app = min((p for _, p in app), default=None)

print(f'total pages: {total}')
print(f'first appendix page: {first_app}')
if first_app:
    print(f'main text: pages 1-{first_app - 1} = {first_app - 1} pages')
    print('UNDER 10' if first_app - 1 <= 10 else
          f'OVER by {first_app - 1 - 10}')

print('\nsection starts:')
for n, (num, p) in sorted(pages.items(), key=lambda kv: (kv[1][1], kv[0])):
    if n.startswith(('sec:', 'app:')) and ':' in n and '.' not in num:
        print(f'  p{p:>3d}  {num:>6s}  {n}')

print('\nfloats:')
for n, (num, p) in sorted(pages.items(), key=lambda kv: kv[1][1]):
    if n.startswith(('tab:', 'fig:')):
        print(f'  p{p:>3d}  {num:>4s}  {n}')

# Which floats land far from where they are cited.
print('\nfloat drift (cited page vs placed page):')
try:
    txt = subprocess.run(['pdftotext', '-layout', f'{JOB}.pdf', '-'],
                         capture_output=True, text=True).stdout
    per_page = txt.split('\f')
    for n, (num, p) in sorted(pages.items(), key=lambda kv: kv[1][1]):
        if not n.startswith(('tab:', 'fig:')):
            continue
        kind = 'Table' if n.startswith('tab:') else 'Figure'
        cited = [i + 1 for i, pg in enumerate(per_page)
                 if re.search(rf'{kind}\s*~?{re.escape(num)}\b', pg)]
        cited = [c for c in cited if c != p] or cited
        if cited:
            drift = min(abs(c - p) for c in cited)
            flag = '   <-- FAR' if drift > 1 else ''
            print(f'  {n:16s} placed p{p:<3d} cited on {cited}{flag}')
except FileNotFoundError:
    print('  (pdftotext unavailable)')
