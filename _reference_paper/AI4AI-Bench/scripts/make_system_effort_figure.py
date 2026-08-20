"""Mean mapped score by system and reasoning effort (replaces the by-system table).

One group of bars per model, one bar per effort level inside it, and the dashed line
at 0.1 is the algorithm each repository already ships. Every bar is the mean of that
configuration's ten task scores.

Reads build/lark/mapped_table.csv; writes Figures/generated/fig_system_effort.pdf.
"""

import csv
import statistics as st
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "build" / "lark" / "mapped_table.csv"
OUT = ROOT / "Figures" / "generated" / "fig_system_effort.pdf"

INK = "#26313C"
GREY = "#AAB2BB"
MCOL = {
    "claude-opus-5": "#E0863F",
    "claude-sonnet-5": "#E3A63C",
    "kimi-k3": "#8C939B",
    "gpt-5.6-sol": "#3E7CB4",
    "gpt-5.6-terra": "#4E9AA6",
    "gpt-5.6-luna": "#57A06C",
}
MLAB = {
    "claude-opus-5": "Claude\nOpus 5",
    "claude-sonnet-5": "Claude\nSonnet 5",
    "kimi-k3": "Kimi K3",
    "gpt-5.6-sol": "GPT-5.6\nSol",
    "gpt-5.6-terra": "GPT-5.6\nTerra",
    "gpt-5.6-luna": "GPT-5.6\nLuna",
}
ORDER = list(MCOL)
EFFORTS = ["none", "low", "medium", "high", "xhigh", "max"]
# effort is read as depth of colour inside a model's own hue
ALPHA = {"none": 0.32, "low": 0.45, "medium": 0.58, "high": 0.72, "xhigh": 0.86, "max": 1.0}

plt.rcParams.update({
    "pdf.fonttype": 42, "font.family": "sans-serif", "font.size": 8.5,
    "text.color": INK, "axes.labelcolor": INK, "axes.edgecolor": "#C8CED5",
    "xtick.color": INK, "ytick.color": INK, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "axes.axisbelow": True,
    "grid.color": "#E1E5EA", "grid.linewidth": 0.6, "figure.facecolor": "white",
})

rows = list(csv.reader(open(SRC)))
cells = defaultdict(list)
for r in rows[1:]:
    cells[(r[0], r[2])] = [float(v) for v in r[3:]]

fig, ax = plt.subplots(figsize=(7.4, 3.4))
xticks, xlabels = [], []
cursor = 0.0
bar_w = 0.8
for model in ORDER:
    levels = [e for e in EFFORTS if (model, e) in cells]
    if not levels:
        continue
    start = cursor
    centers, tops = [], []
    for effort in levels:
        mean = st.mean(cells[(model, effort)])
        ax.bar(cursor, mean, bar_w, color=MCOL[model], alpha=ALPHA[effort],
               edgecolor="white", linewidth=0.6, zorder=3)
        ax.text(cursor, mean + 0.008, f"{mean:.2f}"[1:], ha="center", va="bottom",
                fontsize=6.2, color=INK)
        centers.append(cursor)
        tops.append(mean)
        cursor += bar_w + 0.06
    if len(centers) > 1:
        # the ladder within one model family: effort rising left to right
        ax.plot(centers, tops, "-o", color=MCOL[model], lw=1.3, ms=3.2,
                mec="white", mew=0.8, zorder=5)
    xticks.append((start + cursor - bar_w - 0.06) / 2)
    xlabels.append(MLAB[model])
    cursor += 1.0

ax.axhline(0.1, color=INK, lw=1.2, ls=(0, (4, 3)), zorder=4)

ax.set_xticks(xticks)
ax.set_xticklabels(xlabels, fontsize=8)
ax.set_xlim(-0.8, cursor - 0.9)
ax.set_ylim(0, 0.5)
ax.set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5])
ax.set_ylabel("mean score")
ax.grid(axis="x", visible=False)

# the baseline is named in the legend rather than annotated on the line, where the
# leader line cut across the bars
handles = [
    Line2D([0], [0], marker="s", color="w", markerfacecolor=INK, alpha=ALPHA[e],
           markersize=7, label=e)
    for e in EFFORTS
] + [
    Line2D([0], [0], color=INK, lw=1.2, ls=(0, (4, 3)),
           label="0.1 = the algorithm the repository ships")
]
ax.legend(handles=handles, ncol=7, fontsize=7.2, frameon=False, loc="upper center",
          bbox_to_anchor=(0.5, 1.16), handletextpad=0.25, columnspacing=1.0,
          title=None)

fig.tight_layout()
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT)
print(f"wrote {OUT}")
for model in ORDER:
    row = " ".join(
        f"{e}:{st.mean(cells[(model, e)]):.3f}" for e in EFFORTS if (model, e) in cells
    )
    print(f"  {model:16s} {row}")
