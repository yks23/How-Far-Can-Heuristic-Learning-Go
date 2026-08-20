"""Export the per-cell scatter data used by the AI4AI-Bench site.

One record per (task, model, effort) cell: the mapped score of Section 2.5 and the
output tokens that configuration generated while exploring that task. Also writes the
per-system and per-task means, so the page never recomputes an aggregate in the
browser.

Reads build/lark/mapped_table.csv, build/lark/final_table.csv and
build/behaviour_rows.jsonl; writes ../website/public/ai4ai/data/points.json.
"""

import csv
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "website" / "public" / "ai4ai" / "data" / "points.json"

TASK_LABEL = {
    "openr1_code_livecodebench": ("OpenR1", "supervised fine-tuning"),
    "ragen_sokoban_grpo": ("RAGEN", "multi-turn agentic RL"),
    "opd_math_1p5b": ("OPD", "on-policy distillation"),
    "ultrafeedback_bt_rm_rewardbench": ("BTRM", "reward modelling"),
    "dpo_preference_alignment": ("DPO", "preference optimization"),
    "ddpo_sd15_aesthetic": ("DDPO", "diffusion RL"),
    "openunlearning_tofu_npo_llama3p2_1b": ("NPO", "machine unlearning"),
    "digress_qm9_graph_diffusion": ("DiGress", "discrete graph diffusion"),
    "model_soup_clip_imagenetv2": ("Model Soup", "weight averaging"),
    "owl_wanda_opt6p7b_70pct": ("OWL", "one-shot pruning"),
}
COLUMN = {
    "openr1_code_livecodebench": "OpenR1-Distill",
    "ragen_sokoban_grpo": "RAGEN",
    "opd_math_1p5b": "OPD",
    "ultrafeedback_bt_rm_rewardbench": "BTRM",
    "dpo_preference_alignment": "DPO",
    "ddpo_sd15_aesthetic": "DDPO",
    "openunlearning_tofu_npo_llama3p2_1b": "NPO",
    "digress_qm9_graph_diffusion": "DiGress",
    "model_soup_clip_imagenetv2": "Model Soup",
    "owl_wanda_opt6p7b_70pct": "OWL",
}
MODEL_LABEL = {
    "claude-opus-5": "Claude Opus 5",
    "claude-sonnet-5": "Claude Sonnet 5",
    "kimi-k3": "Kimi K3",
    "gpt-5.6-sol": "GPT-5.6 Sol",
    "gpt-5.6-terra": "GPT-5.6 Terra",
    "gpt-5.6-luna": "GPT-5.6 Luna",
}
EFFORTS = ["none", "low", "medium", "high", "xhigh", "max"]


def main():
    mapped = list(csv.reader(open(ROOT / "build" / "lark" / "mapped_table.csv")))
    header, rows = mapped[0], mapped[1:]
    columns = header[3:]
    score = {}
    harness = {}
    for r in rows:
        harness[(r[0], r[2])] = r[1]
        for column, value in zip(columns, r[3:]):
            score[(column, r[0], r[2])] = float(value)

    raw = list(csv.reader(open(ROOT / "build" / "lark" / "final_table.csv")))
    metric = dict(zip(raw[1][3:13], raw[2][3:13]))
    direction = dict(zip(raw[1][3:13], raw[3][3:13]))
    baseline = dict(zip(raw[1][3:13], raw[4][3:13]))
    cost = {}
    for r in raw[5:34]:
        try:
            cost[(r[0], r[2])] = float(r[13])
        except (IndexError, ValueError):
            cost[(r[0], r[2])] = None

    rawvalue = {}
    for r in raw[5:34]:
        for column, value in zip(raw[1][3:13], r[3:13]):
            rawvalue[(column, r[0], r[2])] = value

    points = []
    for line in open(ROOT / "build" / "behaviour_rows.jsonl"):
        row = json.loads(line)
        column = COLUMN[row["task"]]
        key = (column, row["model"], row["effort"])
        if key not in score:
            continue
        short, family = TASK_LABEL[row["task"]]
        raw_cell = rawvalue.get(key, "")
        points.append({
            "task": row["task"],
            "taskShort": short,
            "family": family,
            "model": row["model"],
            "modelLabel": MODEL_LABEL[row["model"]],
            "harness": harness[(row["model"], row["effort"])],
            "effort": row["effort"],
            "tokens": row["output_tokens"],
            "score": round(score[key], 4),
            "raw": None if raw_cell in ("", "无产出") else float(raw_cell),
            "evals": row["eval_dirs"],
            "patchLines": row["patch_changed"],
            "produced": row["candidate_state"] != "empty" and raw_cell not in ("", "无产出"),
        })

    by_model, by_task = defaultdict(list), defaultdict(list)
    for p in points:
        by_model[p["model"]].append(p["score"])
        by_task[p["taskShort"]].append(p["score"])
    by_effort = defaultdict(list)
    for p in points:
        by_effort[p["effort"]].append(p["score"])

    payload = {
        "generated": "from build/lark/mapped_table.csv and build/behaviour_rows.jsonl",
        "ladder": {"floor": 0, "baseline": 0.1, "optimum": 1.0},
        "points": points,
        "tasks": [
            {
                "id": task,
                "short": TASK_LABEL[task][0],
                "family": TASK_LABEL[task][1],
                "metric": metric[COLUMN[task]],
                "direction": direction[COLUMN[task]],
                "baseline": baseline[COLUMN[task]],
                "mean": round(st.mean(by_task[TASK_LABEL[task][0]]), 3),
            }
            for task in TASK_LABEL
        ],
        "configurations": [
            {
                "model": model,
                "modelLabel": MODEL_LABEL[model],
                "effort": effort,
                "harness": harness[(model, effort)],
                "cost": cost.get((model, effort)),
                "mean": round(st.mean([p["score"] for p in points
                                       if p["model"] == model and p["effort"] == effort]), 4),
                "tokens": sum(p["tokens"] for p in points
                              if p["model"] == model and p["effort"] == effort),
            }
            for (model, effort) in sorted(
                {(p["model"], p["effort"]) for p in points},
                key=lambda k: (list(MODEL_LABEL).index(k[0]), EFFORTS.index(k[1])),
            )
        ],
        "systems": [
            {"id": m, "label": MODEL_LABEL[m], "mean": round(st.mean(xs), 3), "cells": len(xs)}
            for m, xs in sorted(by_model.items(), key=lambda kv: -st.mean(kv[1]))
        ],
        "efforts": [
            {"id": e, "mean": round(st.mean(by_effort[e]), 3), "cells": len(by_effort[e])}
            for e in EFFORTS if e in by_effort
        ],
        "overall": {
            "mean": round(st.mean([p["score"] for p in points]), 3),
            "cells": len(points),
            "belowBaseline": sum(1 for p in points if p["score"] < 0.1),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1))
    print(f"wrote {OUT}: {len(points)} points, mean {payload['overall']['mean']}")


if __name__ == "__main__":
    main()
