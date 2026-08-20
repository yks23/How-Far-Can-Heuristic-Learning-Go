#!/usr/bin/env python3
"""Validate the frozen result snapshot before it is consumed by LaTeX."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    data = json.loads(args.snapshot.read_text())
    assert set(data["tasks"]) == {
        "ddpo_sd15_aesthetic", "digress_qm9_graph_diffusion",
        "dpo_preference_alignment", "ultrafeedback_bt_rm_rewardbench",
        "opd_math_1p5b", "openr1_code_livecodebench",
        "openunlearning_tofu_npo_llama3p2_1b", "owl_wanda_opt6p7b_70pct",
        "model_soup_clip_imagenetv2", "ragen_sokoban_grpo",
    }
    counts = data["gpt_counts"]
    expected = {
        "logical_configurations": 180,
        "terminal_configurations": 172,
        "formal_success": 162,
        "behavior_failure": 10,
        "source_rejected": 8,
        "accepted_artifacts": 473,
        "scored_artifacts": 473,
    }
    assert {k: counts[k] for k in expected} == expected, counts
    gpt_keys = [(r["task_id"], r["model"], r["effort"]) for r in data["gpt_runs"]]
    assert len(gpt_keys) == len(set(gpt_keys)), "duplicate GPT configuration"
    for row in data["gpt_runs"]:
        if row["valid_checkpoint_count"]:
            assert row["best_score"] is not None
            assert row["formal_hours"] is not None
        else:
            assert row["best_score"] is None
    claude = data["claude_artifacts"]
    assert all(r["score"] is not None for r in claude)
    assert all(r["harness"] == "Claude Code" for r in claude)
    receipt_keys = [(r["run_id"], r["progress"]) for r in claude]
    assert len(receipt_keys) == len(set(receipt_keys)), "duplicate Claude checkpoint"
    assert data["claude_counts"]["queue_states"].get("terminal") == 185
    assert data["claude_counts"]["terminal_artifacts"] == 185
    print("validated", args.snapshot)
    print("GPT", counts)
    print("Claude terminal artifacts", len(claude), Counter(r["model"] for r in claude))


if __name__ == "__main__":
    main()
