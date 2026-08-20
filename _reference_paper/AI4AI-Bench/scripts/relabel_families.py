"""Relabel the family rows of Tables/TabFamilies.tex to match the prose of 4.1."""

from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "Tables" / "TabFamilies.tex"
RENAME = {
    "budget, checkpointing and logging": "how long it trains, how often it saves",
    "optimisation knobs": "the training hyperparameters",
    "selection and averaging": "which checkpoint to keep or average",
    "capacity and adapters": "how much trainable capacity, and where",
    "objective surgery": "the loss it optimizes",
    "added supervision": "the supervision it learns from",
    "learning-rule substitution": "the update rule itself",
    "data intervention": "the data it trains on",
}

text = TARGET.read_text()
for old, new in RENAME.items():
    text = text.replace(old, new)
TARGET.write_text(text)
print(f"relabelled {TARGET}")
