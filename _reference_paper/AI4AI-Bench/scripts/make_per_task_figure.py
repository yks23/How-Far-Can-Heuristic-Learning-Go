"""Per-task panel figure: every configuration's score against the task baseline.

Reads the frozen export of the final experiment sheet (build/lark/final_table.csv,
one row per (model, effort) configuration, one column per task) and writes
Figures/generated/fig_per_task.pdf.

One panel per task, because the ten tasks share no scale and no direction: DiGress
and OWL are minimised, the rest maximised, and the metrics range from a perplexity
in the tens to a pass rate in [0, 1]. Each panel therefore carries its own axis and
its own baseline line; what is comparable across panels is only which side of that
line a configuration lands on.

NPO is reported as a single balance score, higher being better.
"""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "build" / "lark" / "final_table.csv"
OUT = ROOT / "Figures" / "generated" / "fig_per_task.pdf"

# Shared Einsia paper palette, as in scripts/make_figures.py.
INK = "#26313C"
GREY = "#AAB2BB"
BLUE = "#3E7CB4"
ORANGE = "#E0863F"
GOLD = "#E3A63C"
TEAL = "#4E9AA6"
GREEN = "#57A06C"

MCOL = {
    "claude-opus-5": ORANGE,
    "claude-sonnet-5": GOLD,
    "kimi-k3": GREY,
    "gpt-5.6-sol": BLUE,
    "gpt-5.6-terra": TEAL,
    "gpt-5.6-luna": GREEN,
}
MLAB = {
    "claude-opus-5": "Claude Opus 5",
    "claude-sonnet-5": "Claude Sonnet 5",
    "kimi-k3": "Kimi K3",
    "gpt-5.6-sol": "GPT-5.6 Sol",
    "gpt-5.6-terra": "GPT-5.6 Terra",
    "gpt-5.6-luna": "GPT-5.6 Luna",
}
EFFORT_ORDER = ["none", "low", "medium", "high", "xhigh", "max"]

plt.rcParams.update(
    {
        "pdf.fonttype": 42,
        "font.family": "sans-serif",
        "font.size": 8,
        "text.color": INK,
        "axes.labelcolor": INK,
        "axes.edgecolor": "#C8CED5",
        "xtick.color": INK,
        "ytick.color": INK,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#E1E5EA",
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "figure.facecolor": "white",
    }
)


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


rows = list(csv.reader(open(SRC)))
tasks = rows[1][3:13]
dirs = list(rows[3][3:13])
base = list(rows[4][3:13])
# NPO reports a single balance score, higher is better; the sheet still carries the
# superseded pair of objectives in its header and baseline cells.
dirs[tasks.index("NPO")] = "↑"
configs = rows[5:34]

# Configurations sorted by model, then by the effort ladder, so every panel puts
# the same configuration at the same x position.
order = sorted(
    range(len(configs)),
    key=lambda i: (
        list(MCOL).index(configs[i][0]),
        EFFORT_ORDER.index(configs[i][2]),
    ),
)

fig, axes = plt.subplots(2, 5, figsize=(7.6, 3.9))
for j, (task, direction, b) in enumerate(zip(tasks, dirs, base)):
    ax = axes[j // 5][j % 5]
    bb = num(b)
    xs, ys, cs = [], [], []
    for x, i in enumerate(order):
        v = num(configs[i][3 + j])
        if v is None:
            continue
        xs.append(x)
        ys.append(v)
        cs.append(MCOL[configs[i][0]])
    ax.scatter(xs, ys, s=22, c=cs, edgecolor="white", linewidth=0.6, zorder=4)
    if bb is not None:
        ax.axhline(bb, color=INK, lw=1.1, ls=(0, (4, 3)), zorder=3)
        wins = sum(
            1 for v in ys if (v > bb if direction == "↑" else v < bb)
        )
        # denominator is every configuration: one that returned nothing did not beat it
        note = f"{wins}/{len(order)} beat baseline"
    else:
        note = "no scalar baseline"
    arrow = "higher is better" if direction == "↑" else "lower is better"
    ax.set_title(f"{task}\n{arrow}", fontsize=7.5, loc="left", color=INK)
    ax.set_xticks([])
    ax.set_xlim(-1, len(order))
    ax.text(
        0.99,
        0.04,
        note,
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=6,
        color=GREY,
    )

handles = [
    Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=6, label=MLAB[m])
    for m, c in MCOL.items()
]
handles.append(Line2D([0], [0], color=INK, lw=1.1, ls=(0, (4, 3)), label="baseline"))
fig.legend(
    handles=handles,
    loc="upper center",
    ncol=4,
    fontsize=8,
    frameon=False,
    bbox_to_anchor=(0.5, 1.0),
)
fig.tight_layout(rect=(0, 0, 1, 0.955))
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT)
print(f"wrote {OUT}")
