#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
CARD_PDF="$ROOT/Figures/cards"
CARD_RAW="$ROOT/build/cards_raw"
CARD_PNG="$ROOT/build/cards_png"
COMPOSE="$ROOT/build/teaser_compose"
OUTPUT="$ROOT/Figures/generated"

mkdir -p "$CARD_PDF" "$CARD_RAW" "$CARD_PNG" "$COMPOSE" "$OUTPUT"
"$PYTHON" "$ROOT/scripts/make_task_cards.py" --output-dir "$CARD_RAW"

for card in "$CARD_RAW"/fig_card_*.pdf; do
  stem="$(basename "$card" .pdf)"
  gs -q -dSAFER -dBATCH -dNOPAUSE -sDEVICE=pdfwrite \
    -dCompatibilityLevel=1.5 -dSubsetFonts=true -dEmbedAllFonts=true \
    -sOutputFile="$CARD_PDF/$stem.pdf" "$card"
done

for card in "$CARD_PDF"/fig_card_*.pdf; do
  stem="$(basename "$card" .pdf)"
  gs -q -dSAFER -dBATCH -dNOPAUSE -sDEVICE=pngalpha -r300 \
    -sOutputFile="$CARD_PNG/$stem.png" "$card"
done

"$PYTHON" "$ROOT/scripts/make_teaser.py" \
  --card-png-dir "$CARD_PNG" \
  --card-pdf-dir "$CARD_PDF" \
  --output-dir "$OUTPUT" \
  --compose-dir "$COMPOSE"

(
  cd "$COMPOSE"
  pdflatex -interaction=nonstopmode -halt-on-error teaser_compose.tex >/dev/null
  pdflatex -interaction=nonstopmode -halt-on-error teaser_compose.tex >/dev/null
)

gs -q -dSAFER -dBATCH -dNOPAUSE -sDEVICE=pdfwrite \
  -dCompatibilityLevel=1.5 -dSubsetFonts=true -dEmbedAllFonts=true \
  -sOutputFile="$OUTPUT/fig_teaser.pdf" "$COMPOSE/teaser_compose.pdf"

echo "$OUTPUT/fig_teaser.pdf"
