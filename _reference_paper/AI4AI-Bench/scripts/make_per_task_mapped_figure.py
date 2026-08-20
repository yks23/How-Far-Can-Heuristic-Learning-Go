"""Per-task mapped score against exploration spend (Figure 2).

Ten panels, one per task: x is the output tokens the configuration generated during
its four-hour exploration of that task (log scale), y is its score after the ladder
of Section 2.5, and the dashed line is 0.1, the score of the repository's own
shipped algorithm. Reads build/lark/mapped_table.csv (written by map_scores.py) and
build/behaviour_rows.jsonl (one record per configuration-task cell).

Writes Figures/generated/fig_per_task_mapped.pdf.
"""

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
MAPPED = ROOT / "build" / "lark" / "mapped_table.csv"
BEHAV = ROOT / "build" / "behaviour_rows.jsonl"
OUT = ROOT / "Figures" / "generated" / "fig_per_task_mapped.pdf"

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
    "claude-opus-5": "Opus 5",
    "claude-sonnet-5": "Sonnet 5",
    "kimi-k3": "Kimi K3",
    "gpt-5.6-sol": "Sol",
    "gpt-5.6-terra": "Terra",
    "gpt-5.6-luna": "Luna",
}
# column order of mapped_table.csv -> the family name the paper uses for the panel
TITLE = {
    "OpenR1-Distill": "Supervised fine-tuning",
    "RAGEN": "Multi-turn agentic RL",
    "OPD": "On-policy distillation",
    "BTRM": "Reward modelling",
    "DPO": "Preference optimisation",
    "DDPO": "Diffusion RL",
    "NPO": "Machine unlearning",
    "DiGress": "Graph diffusion",
    "Model Soup": "Weight averaging",
    "OWL": "One-shot pruning",
}
# the task id used in behaviour_rows.jsonl, per mapped-table column
TASKID = {
    "OpenR1-Distill": "openr1_code_livecodebench",
    "RAGEN": "ragen_sokoban_grpo",
    "OPD": "opd_math_1p5b",
    "BTRM": "ultrafeedback_bt_rm_rewardbench",
    "DPO": "dpo_preference_alignment",
    "DDPO": "ddpo_sd15_aesthetic",
    "NPO": "openunlearning_tofu_npo_llama3p2_1b",
    "DiGress": "digress_qm9_graph_diffusion",
    "Model Soup": "model_soup_clip_imagenetv2",
    "OWL": "owl_wanda_opt6p7b_70pct",
}

plt.rcParams.update(
    {
        "pdf.fonttype": 42,
        "font.family": "sans-serif",
        "font.size": 7,
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

rows = list(csv.reader(open(MAPPED)))
tasks = rows[0][3:13]
mapped = {(r[0], r[2]): [float(v) for v in r[3:13]] for r in rows[1:] if len(r) >= 13}

# output tokens per (model, effort, task); the sheet's model ids carry a dot, the
# behaviour records the same ids, so no renaming is needed.
spend = {}
for line in open(BEHAV):
    b = json.loads(line)
    spend[(b["model"], b["effort"], b["task"])] = b.get("output_tokens")

fig, axes = plt.subplots(2, 5, figsize=(7.1, 3.35), sharex=True)
for j, task in enumerate(tasks):
    ax = axes[j // 5][j % 5]
    for (model, effort), vals in mapped.items():
        tok = spend.get((model, effort, TASKID[task]))
        if not tok:
            continue
        ax.scatter(
            tok, vals[j], s=13, c=MCOL[model], edgecolor="white", linewidth=0.5, zorder=4
        )
    ax.axhline(0.1, color=INK, lw=1.0, ls=(0, (4, 3)), zorder=3)
    ax.set_xscale("log")
    ax.set_title(TITLE[task], fontsize=6.5, loc="left", color=INK, pad=3)
    ax.set_xlim(3e2, 4e5)
    ax.set_xticks([1e3, 1e4, 1e5])
    ax.set_xticklabels(["1k", "10k", "100k"])
    ax.tick_params(labelsize=6.0)
    ax.tick_params(axis="x", which="minor", length=0)
    if j // 5 == 1:
        ax.set_xlabel("output tokens (exploration)", fontsize=6.5)

handles = [
    Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=5, label=MLAB[m])
    for m, c in MCOL.items()
]
handles.append(
    Line2D([0], [0], color=INK, lw=1.0, ls=(0, (4, 3)), label="0.1 = shipped baseline")
)
fig.legend(
    handles=handles,
    loc="upper center",
    ncol=7,
    fontsize=6.8,
    frameon=False,
    bbox_to_anchor=(0.5, 1.005),
    handletextpad=0.3,
    columnspacing=1.0,
)
fig.tight_layout(rect=(0, 0, 1, 0.92))
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT)
print(f"wrote {OUT}")
