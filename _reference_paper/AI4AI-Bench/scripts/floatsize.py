#!/usr/bin/env python3
"""Measure what each float in the paper actually costs in vertical space.

Why this exists: prose word counts and page counts disagreed by several pages,
and guessing which float was responsible was how the previous two compression
passes wasted effort. This measures instead.

Method: build a throwaway document that loads the same preamble, then \input each
float file inside a redefined float environment that captures the body into a box
and writes \ht+\dp to the log. The number reported is the natural height of the
float's content, to which LaTeX adds \textfloatsep when it places it. It is not
"pages saved by deleting this float" -- deleting one lets text reflow -- but it is
the right quantity for deciding which float to shrink first.

Usage (on the machine with the class file):
    /usr/bin/python3.12 tools/floatsize.py
"""
import re
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEXTHEIGHT_PT = 659.82  # from style/company_light, confirmed in the .log


def preamble(main: pathlib.Path) -> str:
    src = main.read_text()
    return src.split(r"\begin{document}")[0]


def build_probe(files: list[str], main: pathlib.Path) -> str:
    body = []
    for f in files:
        stem = pathlib.Path(f).stem
        body.append(
            rf"""
\begingroup
\renewenvironment{{table}}[1][]{{\setbox0\vbox\bgroup\hsize\textwidth}}%
  {{\egroup\typeout{{FLOATSIZE {stem} \the\ht0 \space \the\dp0}}}}
\renewenvironment{{table*}}[1][]{{\setbox0\vbox\bgroup\hsize\textwidth}}%
  {{\egroup\typeout{{FLOATSIZE {stem} \the\ht0 \space \the\dp0}}}}
\renewenvironment{{figure}}[1][]{{\setbox0\vbox\bgroup\hsize\textwidth}}%
  {{\egroup\typeout{{FLOATSIZE {stem} \the\ht0 \space \the\dp0}}}}
\renewenvironment{{figure*}}[1][]{{\setbox0\vbox\bgroup\hsize\textwidth}}%
  {{\egroup\typeout{{FLOATSIZE {stem} \the\ht0 \space \the\dp0}}}}
\input{{{f}}}
\endgroup
"""
        )
    return preamble(main) + r"\begin{document}" + "\n".join(body) + r"\end{document}"


def main() -> int:
    main_tex = ROOT / "main.tex"
    floats = [
        "Tables/TabTasks",
        "Tables/TabMedal",
        "Tables/TabMain",
        "Figures/FigPipeline",
        "Tables/TabLifecycle",
        "Tables/TabEffort",
        "Tables/TabMetricKeys",
        "Tables/TabAuditChecklist",
        "Tables/TabBaselines",
        "Tables/TabReduction",
        "Tables/TabBehaviors",
        "Tables/TabDDPO",
        "Tables/TabRagen",
        "Figures/FigTaskCards",
    ]
    probe = ROOT / "_floatprobe.tex"
    probe.write_text(build_probe(floats, main_tex))
    proc = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-jobname=_floatprobe", probe.name],
        cwd=ROOT, capture_output=True, text=True,
    )
    log = (ROOT / "_floatprobe.log")
    text = log.read_text(errors="replace") if log.exists() else proc.stdout
    # pdflatex wraps \typeout at 79 columns, so rejoin before matching.
    flat = re.sub(r"\n", "", text)
    hits = re.findall(r"FLOATSIZE (\S+?) ([\d.]+)pt ([\d.]+)pt", flat)
    if not hits:
        print("no FLOATSIZE lines found; probe build failed", file=sys.stderr)
        print(text[-2500:], file=sys.stderr)
        return 1
    print(f"{'float':26s} {'height':>9s} {'% textheight':>13s}")
    total = 0.0
    for name, ht, dp in hits:
        h = float(ht) + float(dp)
        total += h
        print(f"{name:26s} {h:8.1f}pt {100*h/TEXTHEIGHT_PT:12.1f}%")
    print(f"{'TOTAL':26s} {total:8.1f}pt {total/TEXTHEIGHT_PT:12.2f} pages")
    for f in ROOT.glob("_floatprobe.*"):
        f.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
