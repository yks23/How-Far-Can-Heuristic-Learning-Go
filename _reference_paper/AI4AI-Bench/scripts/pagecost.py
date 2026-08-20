#!/usr/bin/env python3
"""Report how much vertical space each main-text section actually occupies.

Why this exists: pages.py gives section start pages, which quantizes to whole
pages and hides where the space goes inside a page. floatsize.py gives float
heights. Neither answers "if I cut 200 words from section N, does the page count
drop", because the answer depends on how far into its last page each section
already runs. This measures that: it writes a \typeout at every \section and
\subsection with the current page number and the remaining vertical space on the
page, so a section's true cost is (pages spanned) minus (slack at its end).

Method: \AddToHook on \section injects \typeout{PAGECOST <label> <page> <goal
minus pagetotal>}. \pagetotal is only meaningful in vertical mode between
paragraphs, which is exactly where a \section lands, so the reading is the height
already committed to the current page when the section begins.

Usage (on the machine with the class file):
    /usr/bin/python3.12 tools/pagecost.py
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEXTHEIGHT_PT = 659.82

PROBE = r"""
\makeatletter
\newcommand{\PC@report}[1]{%
  \typeout{PAGECOST #1 p\thepage\space used=\the\pagetotal\space goal=\the\pagegoal}}
\let\PC@oldsection\section
\renewcommand{\section}{\@ifstar{\PC@star}{\PC@nostar}}
\newcommand{\PC@star}[1]{\PC@report{STAR}\PC@oldsection*{#1}}
\newcommand{\PC@nostar}[1]{\PC@report{SEC}\PC@oldsection{#1}}
\let\PC@oldsubsection\subsection
\renewcommand{\subsection}[1]{\PC@report{SUB}\PC@oldsubsection{#1}}
\makeatother
"""


def main() -> int:
    src = (ROOT / "main.tex").read_text()
    # Inject after \begin{document} so the class has finished setting up.
    marked = src.replace(r"\begin{document}", r"\begin{document}" + PROBE, 1)
    probe = ROOT / "_pagecost.tex"
    probe.write_text(marked)
    subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-jobname=_pagecost", probe.name],
        cwd=ROOT, capture_output=True, text=True,
    )
    log = ROOT / "_pagecost.log"
    text = log.read_text(errors="replace") if log.exists() else ""
    flat = re.sub(r"\n", "", text)
    hits = re.findall(
        r"PAGECOST (\w+) p(\d+) used=([\d.-]+)pt goal=([\d.-]+)pt", flat)
    if not hits:
        print("no PAGECOST lines; probe build failed", file=sys.stderr)
        print(text[-2000:], file=sys.stderr)
        return 1
    print(f"{'kind':6s} {'page':>5s} {'used on page':>13s} {'slack':>9s}")
    for kind, page, used, goal in hits:
        u, g = float(used), float(goal)
        slack = g - u if g > 0 else TEXTHEIGHT_PT - u
        print(f"{kind:6s} {page:>5s} {u:11.1f}pt {slack:7.1f}pt")
    for f in ROOT.glob("_pagecost.*"):
        f.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
