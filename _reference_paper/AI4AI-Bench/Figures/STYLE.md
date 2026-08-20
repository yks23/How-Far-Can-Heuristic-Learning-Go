# Figure Style

The paper follows the shared visual language used by the Frontier-Eng and
BrowserBC papers: warm paper tints, slate typography, muted categorical color,
and orange reserved for the agent/action or the leading result.

## Palette

- Ink: `#26313C`
- Secondary text: `#6B7280`
- Blue: `#3E7CB4`
- Mid blue: `#8FB2D6`
- Teal: `#4E9AA6`
- Green: `#57A06C`
- Orange: `#E0863F`
- Gold: `#E3A63C`
- Warm panel: `#FBF2E9`
- Warm header: `#F1ECE3`
- Neutral panel: `#F7F8FA`
- Border/grid: `#DCE0E5`

## Rules

- Use slate for text and major rules; do not use saturated navy as a page-wide
  header color.
- Use orange sparingly for agent actions, the leader, and the primary outcome.
- Use blue/teal/green for structural or categorical distinctions.
- Keep chart backgrounds white, grid lines thin, legends unboxed, and labels
  direct where possible.
- Use DejaVu Sans for generated plots and cards. Keep all text at least 8 pt at
  the final publication size.
- Export vector PDF with embedded TrueType or Type 1 fonts. Type 3 fonts and
  rasterized full figures are not accepted.

## Build

```bash
python3 scripts/make_figures.py
scripts/build_teaser.sh
```

The editable source for Figure 2 is
`Figures/generated/fig_pipeline_editable.pptx`; its PDF export remains
`Figures/generated/fig_pipeline.pdf`.
