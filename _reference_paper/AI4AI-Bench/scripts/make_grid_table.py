"""Generate the two experiment tables from the frozen export of the sheet.

Tables/TabFinalGrid.tex  -- every configuration on every task in raw metric units
Tables/TabMappedGrid.tex -- the same cells after the Section 2.5 ladder

Both share one visual language. A cell's background reports its mapped score: below
0.1 (worse than the repository's own recipe) light red, 0.1 to 0.4 yellow, above 0.4
light green. Bold marks the best cell in a task, once per column.

The raw table also carries the exploration cost of each configuration, and closes
with the three rows that define the ladder: the optimum, the uninformative point,
and the progress coordinate.
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "build" / "lark" / "final_table.csv"
MAPPED = ROOT / "build" / "lark" / "mapped_table.csv"
OUT_RAW = ROOT / "Tables" / "TabFinalGrid.tex"
OUT_MAP = ROOT / "Tables" / "TabMappedGrid.tex"

SHORT = {"OpenR1-Distill": "OpenR1", "Model Soup": "Soup"}
MLAB = {
    "claude-opus-5": "Claude Opus 5",
    "claude-sonnet-5": "Claude Sonnet 5",
    "kimi-k3": "Kimi K3",
    "gpt-5.6-sol": "GPT-5.6 Sol",
    "gpt-5.6-terra": "GPT-5.6 Terra",
    "gpt-5.6-luna": "GPT-5.6 Luna",
}
ORDER = list(MLAB)
EFFORT = ["none", "low", "medium", "high", "xhigh", "max"]
# One mark per model vendor, set before the model name.
def icon(model):
    slug = {"claude-opus-5": "claude", "claude-sonnet-5": "claude", "kimi-k3": "kimi"}.get(
        model, "openai"
    )
    return r"\raisebox{-0.15ex}{\includegraphics[height=1.5ex]{logos/%s}}" % slug
# the ladder, as instantiated in scripts/map_scores.py
LADDER = {
    "OpenR1-Distill": ("1", "0", r"$x$"),
    "RAGEN": ("1", "0", r"$x$"),
    "OPD": ("1", "0", r"$x$"),
    "BTRM": ("100", "50", r"$x$"),
    "DPO": ("1", "0", r"$x$"),
    "DDPO": ("23.23", "$-12.76$", r"$x$"),
    "NPO": ("2.08", "0", r"$x$"),
    "DiGress": ("0", r"$\infty$", r"$-x$"),
    "Model Soup": ("1", "0", r"$x$"),
    "OWL": ("1", r"$\infty$", r"$-\log x$"),
}


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def fmt(v):
    if v is None:
        return "--"
    if abs(v) >= 10:
        return f"{v:.1f}"
    if abs(v) >= 1:
        return f"{v:.2f}"
    return f"{v:.3f}"


def band(m):
    """Background for a mapped score."""
    if m is None:
        return ""
    if m < 0.1:
        return r"\cellcolor{bandlow}"
    if m <= 0.4:
        return r"\cellcolor{bandmid}"
    return r"\cellcolor{bandhigh}"


rows = list(csv.reader(open(SRC)))
tasks = rows[1][3:13]
dirs = list(rows[3][3:13])
dirs[tasks.index("NPO")] = "↑"  # single balance score, higher is better
base = list(rows[4][3:13])
configs = sorted(rows[5:34], key=lambda r: (ORDER.index(r[0]), EFFORT.index(r[2])))

mapped_rows = list(csv.reader(open(MAPPED)))[1:]
mapped = {(r[0], r[2]): [float(v) for v in r[3:]] for r in mapped_rows}

# best cell per task, in raw units, under the task's direction
best_idx = []
for j, d in enumerate(dirs):
    vals = [(num(r[3 + j]), i) for i, r in enumerate(configs)]
    vals = [(v, i) for v, i in vals if v is not None]
    best_idx.append(max(vals)[1] if d == "↑" else min(vals)[1])

# best row average in the mapped table, bolded in its avg column
row_avg = [sum(mapped[(r[0], r[2])]) / len(tasks) for r in configs]
best_avg_idx = max(range(len(row_avg)), key=lambda i: row_avg[i])


def header(kind):
    arrow = lambda d: "uparrow" if d == "↑" else "downarrow"
    if kind == "raw":
        cols = " & ".join(
            f"\\textbf{{{SHORT.get(t, t)}}}\\,$\\{arrow(d)}$" for t, d in zip(tasks, dirs)
        )
        return r"& \textbf{System} & \textbf{Harness} & \textbf{Effort} & " + cols + r" & \textbf{Cost (USD)}\\"
    cols = " & ".join(f"\\textbf{{{SHORT.get(t, t)}}}" for t in tasks)
    return r"& \textbf{System} & \textbf{Harness} & \textbf{Effort} & " + cols + r" & \textbf{avg}\\"


def body(kind):
    out, prev = [], None
    for i, r in enumerate(configs):
        if prev is not None and r[0] != prev:
            out.append(r"\addlinespace[2pt]")
        prev = r[0]
        ms = mapped[(r[0], r[2])]
        cells = []
        for j, t in enumerate(tasks):
            m = ms[j]
            if kind == "raw":
                v = num(r[3 + j])
                text = fmt(v)
            else:
                text = f"{m:.3f}"
            if i == best_idx[j]:
                text = f"\\textbf{{{text}}}"
            cells.append(f"{band(m)}{text}")
        if kind == "raw":
            cost = num(r[13])
            tail = "--" if cost is None else f"{cost:.0f}"
        else:
            tail = f"{sum(ms)/len(ms):.3f}"
            if i == best_avg_idx:
                tail = f"\\textbf{{{tail}}}"
        out.append(
            f"{icon(r[0])} & {MLAB[r[0]]} & {r[1]} & \\texttt{{{r[2]}}} & "
            + " & ".join(cells)
            + f" & {tail}"
            + r" \\"
        )
    return out


def emit(kind, path, caption, label):
    lines = ["% Generated by scripts/make_grid_table.py -- do not edit by hand."]
    lines += [r"\begin{table}[t]", r"\centering", caption, f"\\label{{{label}}}", r"\scriptsize"]
    lines += [r"\begin{adjustbox}{max width=\linewidth}"]
    lines += [r"\begin{tabular}{llll" + "r" * (len(tasks) + 1) + "}", r"\toprule", header(kind), r"\midrule"]
    if kind == "raw":
        lines.append(
            r"& \emph{Baseline} & \na{} & \na{} & "
            + " & ".join(fmt(num(b)) for b in base)
            + r" & \na{} \\"
        )
        lines.append(r"\midrule")
    lines += body(kind)
    lines.append(r"\midrule")
    if kind == "raw":
        for name, k in ((r"\emph{Optimum} $x^{\ast}$", 0), (r"\emph{Uninformative} $x_{\perp}$", 1),
                        (r"\emph{Coordinate} $\varphi$", 2)):
            lines.append(
                f"\\multicolumn{{4}}{{l}}{{{name}}} & "
                + " & ".join(LADDER[t][k] for t in tasks)
                + r" & \na{} \\"
            )
    else:
        lines = lines[:-1]  # no summary row: the means live in their own tables
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{adjustbox}", r"\end{table}"]
    path.write_text("\n".join(lines) + "\n")
    print(f"wrote {path}")


emit(
    "raw",
    OUT_RAW,
    r"\caption{\textbf{Every configuration on every task, in the metric's own units.} Rows are the 29 "
    r"(model, harness, effort) configurations; \textbf{\$} is what the four hours of exploration cost. "
    r"\emph{Baseline} is the score of the repository's own code under the identical procedure "
    r"(\S\ref{sec:baselines}). Backgrounds report the mapped score of \S\ref{sec:scoring}: "
    r"\colorbox{bandlow}{below $0.1$} is worse than that baseline, \colorbox{bandmid}{$0.1$ to $0.4$} "
    r"beats it, \colorbox{bandhigh}{above $0.4$} closes more than a third of the distance to the "
    r"optimum. \textbf{Bold} marks the best cell in a column, and a dash a configuration that returned "
    r"nothing trainable. The last three rows give the ladder each column is scored on.}",
    "tab:grid",
)
emit(
    "map",
    OUT_MAP,
    r"\caption{\textbf{The same cells after the ladder of \S\ref{sec:scoring}.} $0.1$ is the "
    r"repository's own recipe and $1.0$ the task optimum, so a score states how much of the remaining "
    r"distance a submission closed; a configuration that returned nothing scores $0$. Backgrounds "
    r"and bold follow Table~\ref{tab:grid}; per-system and per-task means are in "
    r"Figure~\ref{fig:bysystem}.}",
    "tab:mapped",
)


# ---------------------------------------------------------------- summary tables
def summary_tables():
    import statistics as st

    per_model, per_task = {}, {}
    for r in configs:
        per_model.setdefault(r[0], []).extend(mapped[(r[0], r[2])])
    for j, t in enumerate(tasks):
        per_task[t] = [mapped[(r[0], r[2])][j] for r in configs]

    lines = ["% Generated by scripts/make_grid_table.py -- do not edit by hand.",
             r"\begin{table}[t]", r"\centering",
             r"\caption{\textbf{Mean score by system.} The mapped score of \S\ref{sec:scoring} "
             r"averaged over that system's cells, where $0.1$ is the algorithm each repository ships "
             r"and $1.0$ the task optimum. Every system in the study sits inside the lowest fifth of "
             r"the scale.}",
             r"\label{tab:bysystem}", r"\small",
             r"\begin{tabular}{llr}", r"\toprule",
             r"& \textbf{System} & \textbf{Mean score} \\", r"\midrule"]
    for m, xs in sorted(per_model.items(), key=lambda kv: -st.mean(kv[1])):
        lines.append(f"{icon(m)} & {MLAB[m]} & {st.mean(xs):.3f} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    (ROOT / "Tables" / "TabBySystem.tex").write_text("\n".join(lines) + "\n")

    print("wrote the per-system summary table")


summary_tables()
