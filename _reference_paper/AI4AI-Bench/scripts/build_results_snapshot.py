#!/usr/bin/env python3
"""Build the compact, read-only result snapshot used by the manuscript.

The script deliberately consumes exported Feishu CSV envelopes and final-test
receipts, rather than importing anything from a training directory at LaTeX
build time.  Missing values stay null and are never converted to zero.
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_BY_SHEET = {
    "DDPO": "ddpo_sd15_aesthetic",
    "DiGress": "digress_qm9_graph_diffusion",
    "DPO": "dpo_preference_alignment",
    "Model_Soup": "model_soup_clip_imagenetv2",
    "OPD": "opd_math_1p5b",
    "OpenR1": "openr1_code_livecodebench",
    "NPO": "openunlearning_tofu_npo_llama3p2_1b",
    "OWL": "owl_wanda_opt6p7b_70pct",
    "RAGEN": "ragen_sokoban_grpo",
    "BTRM": "ultrafeedback_bt_rm_rewardbench",
}


TASK_METADATA: dict[str, dict[str, Any]] = {
    "ddpo_sd15_aesthetic": {
        "name": "DDPO",
        "family": "generative modeling",
        "starting_artifact": "Stable Diffusion v1.5 + LoRA recipe",
        "metric": "mean_aesthetic_score_final256",
        "direction": "maximize",
        "base_score": 5.397311,
        "current_recipe_score": 5.526373,
        "artifact": "Diffusers adapter",
        "sample_count": 256,
    },
    "digress_qm9_graph_diffusion": {
        "name": "DiGress",
        "family": "generative modeling",
        "starting_artifact": "QM9 discrete graph diffusion model",
        "metric": "qm9_test_nll",
        "direction": "minimize",
        "base_score": 78.05,
        "current_recipe_score": 69.57,
        "artifact": "graph checkpoint",
        "sample_count": 10000,
    },
    "dpo_preference_alignment": {
        "name": "DPO",
        "family": "preference optimization",
        "starting_artifact": "merged Zephyr/Mistral-7B policy",
        "metric": "ifeval_strict_accuracy_hidden413",
        "direction": "maximize",
        "base_score": 164 / 413,
        "current_recipe_score": 210 / 413,
        "artifact": "PEFT or merged language model",
        "sample_count": 413,
    },
    "ultrafeedback_bt_rm_rewardbench": {
        "name": "BTRM",
        "family": "reward modeling",
        "starting_artifact": "Mistral-7B-Instruct-v0.2 + reward head",
        "metric": "rewardbench_v1_score",
        "direction": "maximize",
        "base_score": None,
        "current_recipe_score": 74.568936,
        "artifact": "reward model with scalar head",
        "sample_count": 2985,
    },
    "opd_math_1p5b": {
        "name": "OPD",
        "family": "language-model post-training",
        "starting_artifact": "DeepSeek-R1-Distill-Qwen-1.5B student",
        "metric": "aime24_25_at32",
        "direction": "maximize",
        "base_score": 484 / 1920,
        "current_recipe_score": 820 / 1920,
        "artifact": "language-model checkpoint",
        "sample_count": 60,
    },
    "openr1_code_livecodebench": {
        "name": "OpenR1",
        "family": "language-model post-training",
        "starting_artifact": "Qwen2.5-Coder-1.5B-Instruct",
        "metric": "livecodebench_v6_pass_at_1_first128",
        "direction": "maximize",
        "base_score": 13 / 128,
        "current_recipe_score": 17 / 128,
        "artifact": "language-model checkpoint or adapter",
        "sample_count": 128,
    },
    "openunlearning_tofu_npo_llama3p2_1b": {
        "name": "NPO",
        "family": "language-model post-training",
        "starting_artifact": "Llama-3.2-1B-Instruct",
        "metric": "Extraction / MU",
        "direction": "mixed",
        "base_score": {"extraction": 0.707805, "mu": 0.597131},
        "current_recipe_score": {"extraction": 0.063436, "mu": 0.478673},
        "artifact": "unlearned language model",
        "sample_count": None,
    },
    "owl_wanda_opt6p7b_70pct": {
        "name": "OWL",
        "family": "compression",
        "starting_artifact": "facebook/OPT-6.7B dense model",
        "metric": "wikitext2_test_perplexity",
        "direction": "minimize",
        "base_score": 10.860456,
        "current_recipe_score": 53.358987,
        "artifact": "70% sparse pruned model",
        "sample_count": None,
    },
    "model_soup_clip_imagenetv2": {
        "name": "Model Soup",
        "family": "construction and merging",
        "starting_artifact": "72 CLIP ingredient checkpoints",
        "metric": "imagenetv2_top1_full10000",
        "direction": "maximize",
        "base_score": 0.6874,
        "current_recipe_score": 0.6859,
        "artifact": "soup state dict",
        "sample_count": 10000,
    },
    "ragen_sokoban_grpo": {
        "name": "RAGEN",
        "family": "agent and reinforcement learning",
        "starting_artifact": "Qwen2.5-3B-Instruct RL policy",
        "metric": "held_out_512_board_solve_rate",
        "direction": "maximize",
        "base_score": 60 / 512,
        "current_recipe_score": 87 / 512,
        "artifact": "merged Sokoban policy",
        "sample_count": 512,
    },
}


def number(value: str | None) -> float | int | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        result = float(value.replace(",", ""))
    except ValueError:
        return None
    return int(result) if result.is_integer() else result


def row_from_annotated(line: str) -> tuple[int, list[str]] | None:
    match = re.match(r"\[row=(\d+)\] (.*)$", line)
    if not match:
        return None
    return int(match.group(1)), next(csv.reader([match.group(2)]))


def build_gpt_rows(gpt_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    allowed_efforts = {"none", "low", "medium", "high", "xhigh", "max"}
    for path in sorted(gpt_dir.glob("*.json")):
        if path.name == "overview.json":
            continue
        task_id = TASK_BY_SHEET.get(path.stem)
        if not task_id:
            continue
        data = json.loads(path.read_text())["data"]
        for line in data["annotated_csv"].splitlines():
            parsed = row_from_annotated(line)
            if not parsed:
                continue
            row_number, values = parsed
            if row_number < 24 or len(values) < 27:
                continue
            model, effort = values[0].strip(), values[1].strip()
            if not model.startswith("gpt-5.6-") or effort not in allowed_efforts:
                continue
            scores = [number(values[i]) for i in (6, 9, 12)]
            progress = [number(values[i]) for i in (15, 16, 17)]
            accepted = re.search(r"accepted=(\d+)", values[22] if len(values) > 22 else "")
            rows.append(
                {
                    "task_id": task_id,
                    "model": model,
                    "harness": "Codex",
                    "effort": effort,
                    "formal_state": values[18],
                    "failure_class": values[19],
                    "best_score": number(values[2]),
                    "best_checkpoint": values[5] if values[5].startswith("ckpt") else None,
                    "scores": scores,
                    "progress": progress,
                    "valid_checkpoint_count": int(accepted.group(1)) if accepted else 0,
                    "formal_hours": number(values[20]),
                    "budget_utilization": values[21] if len(values) > 21 else "",
                    "final_scoring": values[23] if len(values) > 23 else "",
                    "run_id": values[25],
                    "source_row": row_number,
                }
            )
    return rows


def build_claude_rows(claude_dir: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rows: list[dict[str, Any]] = []
    state_counts: dict[str, int] = {}
    for path in sorted(claude_dir.glob("jobs/*/receipt.json")):
        receipt = json.loads(path.read_text())
        state = receipt.get("state", "unknown")
        state_counts[state] = state_counts.get(state, 0) + 1
        if state != "terminal" or receipt.get("result", {}).get("runner_exit") != 0:
            continue
        summary_path = Path(receipt.get("result", {}).get("summary", ""))
        summary: dict[str, Any] = {}
        if summary_path.is_file():
            try:
                summary = json.loads(summary_path.read_text())
            except json.JSONDecodeError:
                summary = {}
        run_id = receipt["run_id"]
        task_id, model, effort, *_ = run_id.split("__")
        rows.append(
            {
                "task_id": summary.get("task_id", task_id),
                "model": model,
                "harness": "Claude Code",
                "effort": effort,
                "run_id": run_id,
                "progress": receipt.get("progress"),
                "score": summary.get("score", receipt.get("result", {}).get("score")),
                "metric": summary.get("metric"),
                "direction": summary.get("direction"),
                "sample_count": summary.get("n"),
                "stderr": summary.get("stderr"),
                "status": summary.get("status"),
                "artifact_sha256": summary.get("artifact_sha256"),
                "source_receipt": str(path),
            }
        )
    return rows, state_counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpt-dir", type=Path, required=True)
    parser.add_argument("--claude-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gpt-revision", type=int, default=277)
    args = parser.parse_args()

    gpt_rows = build_gpt_rows(args.gpt_dir)
    claude_rows, claude_states = build_claude_rows(args.claude_dir)
    formal_counts = {
        "logical_configurations": len(gpt_rows),
        # A source-rejected patch has a populated status cell in the Feishu
        # export, but never entered formal replay.  The published terminal
        # denominator is therefore formal success plus behavior failure.
        "terminal_configurations": sum(
            r["failure_class"] != "source_rejected" for r in gpt_rows
        ),
        "formal_success": sum(r["valid_checkpoint_count"] > 0 for r in gpt_rows),
        "behavior_failure": sum(r["failure_class"] == "behavior" and r["valid_checkpoint_count"] == 0 for r in gpt_rows),
        "source_rejected": sum(r["failure_class"] == "source_rejected" for r in gpt_rows),
        "accepted_artifacts": sum(r["valid_checkpoint_count"] for r in gpt_rows),
        "scored_artifacts": sum(r["valid_checkpoint_count"] for r in gpt_rows),
    }
    snapshot = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "gpt": {
                "kind": "Feishu Sheets export",
                "revision": args.gpt_revision,
                "scope": "v1.5 task detail rows",
            },
            "claude": {
                "kind": "final-test receipt snapshot",
                "scope": "terminal receipts with runner_exit=0",
                "queue_states": claude_states,
            },
        },
        "gpt_counts": formal_counts,
        "claude_counts": {
            "terminal_artifacts": len(claude_rows),
            "queue_states": claude_states,
        },
        "tasks": TASK_METADATA,
        "gpt_runs": gpt_rows,
        "claude_artifacts": claude_rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
