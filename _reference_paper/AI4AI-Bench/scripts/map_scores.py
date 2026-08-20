"""Map every raw task metric onto the common [0,1] ladder of Section 2.5.

Three anchors per task: 0 is the task's theoretical worst, 0.1 is the score of the
repository's own recipe (the baseline), and 1.0 is the task's theoretical best.

    above the baseline   s = 0.1 + 0.9 * (x - base) / (best - base)
    below the baseline   s = 0.1 * (x - worst) / (base - worst)

For DiGress and OWL the worse side is unbounded (an NLL and a perplexity have no
upper limit), so it uses s = 0.1 * base / x, which is exactly 0.1 at the baseline
and tends to 0 as x grows. OWL is interpolated in log space, since a perplexity is
the exponential of a cross-entropy: without that, 53.4 -> 16.2 would read as 71%
of the distance to the optimum when it is 30%.

A configuration that returned nothing scores 0.

Extremes and baselines are read from the experiment sheet (rows 5, 35, 36 of
Sheet1); this script keeps them in one table so the mapping can be rerun offline.
Reads build/lark/final_table.csv, writes build/lark/mapped_table.csv.
"""

import collections
import csv
import math
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "build" / "lark" / "final_table.csv"
OUT = ROOT / "build" / "lark" / "mapped_table.csv"

INF = float("inf")
# task: (direction, theoretical worst, theoretical best, log-scale?)
LADDER = {
    "OpenR1-Distill": ("max", 0.0, 1.0, False),
    "RAGEN": ("max", 0.0, 1.0, False),
    "OPD": ("max", 0.0, 1.0, False),
    "BTRM": ("max", 50.0, 100.0, False),  # 50 is the pairwise-preference chance level
    "DPO": ("max", 0.0, 1.0, False),
    "DDPO": ("max", -12.7590, 23.2323, False),
    "NPO": ("max", 0.0, 2.0824, False),
    "DiGress": ("min", INF, 0.0, False),
    "Model Soup": ("max", 0.0, 1.0, False),
    "OWL": ("min", INF, 1.0, True),
}


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def score(task, x, base):
    direction, worst, best, log_scale = LADDER[task]
    better = x >= base if direction == "max" else x <= base
    if better:
        u, ub, uw = (math.log(x), math.log(base), math.log(best)) if log_scale else (x, base, best)
        if ub == uw:
            return 1.0
        return min(1.0, 0.1 + 0.9 * (u - ub) / (uw - ub))
    if worst == INF:  # unbounded worse side: converge to 0 without an anchor
        return max(0.0, 0.1 * base / x)
    return max(0.0, 0.1 * (x - worst) / (base - worst))


def build():
    rows = list(csv.reader(open(SRC)))
    tasks = rows[1][3:13]
    base = {t: num(b) for t, b in zip(tasks, rows[4][3:13])}
    configs = rows[5:34]

    print(f"{'task':15s} {'dir':4s} {'worst':>10s} {'best':>10s} {'baseline':>10s}  scale")
    for t in tasks:
        d, w, b, lg = LADDER[t]
        print(
            f"{t:15s} {d:4s} {str(w):>10s} {str(b):>10s} {base[t]:10.4f}  "
            f"{'log' if lg else 'linear'}"
        )

    out = [["model", "harness", "effort"] + tasks]
    for r in configs:
        line = [r[0], r[1], r[2]]
        for j, t in enumerate(tasks):
            v = num(r[3 + j])
            line.append(0.0 if v is None else round(score(t, v, base[t]), 4))
        out.append(line)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    csv.writer(open(OUT, "w", newline="")).writerows(out)

    per_model, per_task = collections.defaultdict(list), collections.defaultdict(list)
    for line in out[1:]:
        for t, v in zip(tasks, line[3:]):
            per_model[line[0]].append(v)
            per_task[t].append(v)
    print("\nmapped score, average by model")
    for m, xs in sorted(per_model.items(), key=lambda kv: -st.mean(kv[1])):
        print(f"  {m:16s} n={len(xs):3d}  avg={st.mean(xs):.3f}")
    print("\nmapped score, average by task")
    for t in tasks:
        print(f"  {t:15s} avg={st.mean(per_task[t]):.3f}")
    print("\ncheck: OWL 16.2 ->", round(score("OWL", 16.2, base["OWL"]), 4), "(sheet says 30% of the way)")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
