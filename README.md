# How Far Can Heuristic Learning Go?

Draft paper. Characterizing performance ceilings, complexity, and sample
efficiency of heuristic learning in large-scale real-world competitive games.

## Build

```bash
latexmk -pdf -outdir=build main.tex
```

Output is `build/main.pdf`. Compiles with pdfLaTeX; there is no Makefile.

On Overleaf, pick `main.tex` as the main document and leave the compiler on
pdfLaTeX. Note that pdfLaTeX cannot typeset CJK without `CJKutf8`, which is why
every prose-valued entry in `numbers.tex` is English-only.

## Every number lives in `numbers.tex`

The body never writes a literal number. It writes `\val{key}`, and the value is
defined once in `numbers.tex`. Two reasons: a figure that appears in the
abstract, a table, and the discussion can only contradict itself if it is typed
three times, and a provisional figure has to stay visibly provisional.

```latex
\defval{editions}{30}        % measured. prints plain.
\defTBD{pct}{XX}             % not measured. prints in accent bold, and is
                             % listed under "Outstanding measurements".
```

Use `\val{pct}` in the text. An undefined key prints a red marker and raises a
LaTeX warning rather than failing silently.

Before submission, set `\togglefalse{hldraft}` in `numbers.tex`. Every
placeholder then prints as though it were real — which is exactly why the
outstanding-measurements list at the end of the PDF must read empty first.

Keys hold bare quantities, never connective words. `\defTBD{pct}{XX}`, not
`XXth`: baking English grammar into a value makes it unusable elsewhere.

## Layout

- `main.tex` — title metadata, abstract, and `\input` assembly
- `numbers.tex` — every quantitative claim, plus `\val`, `\defTBD`, `\printTBD`
- `sections/01`–`08` — one file per section. Each opens with a comment block
  stating that section's scope and the traps to avoid in it; read it before
  editing the section.
- `refs.bib` — every entry annotated with what argument it supports and what
  caution applies to it
- `style/company_light.cls` — the active document class
- `assets/`, `scripts/` — figures, and the helpers that generated the title-block
  measurements
- `_reference_paper/` — a formatting reference, not part of the build

`kexiearticle.sty` is not loaded by anything. It is the original SAST template,
requires XeLaTeX, and is kept only for reference.

## Conventions

The introduction's argument runs as one chain, and its header comment enumerates
the links along with the invariants that keep them in order. Two are worth
repeating here because they have each been violated once:

- The complexity axis is `K(pi_good)`, the description length of a symbolic
  policy good enough to win. Never rule length. Go has short rules and no
  compact symbolic policy, which is the whole point.
- Agent self-improvement decay has already been measured elsewhere. Concede that
  and say what it lacks; do not claim this ceiling has never been studied.

Author lists in `refs.bib` are fetched from the source, never reconstructed from
memory. An entry with no `author` field renders as a truncated fragment like
`(fro, 2026)` and BibTeX only warns about it, so it ships silently if unchecked.

## Verifying a build

```bash
latexmk -pdf -interaction=nonstopmode -outdir=build main.tex
grep -c "Undefined number key\|Citation.*undefined" build/main.log   # want 0
grep -ci "warning--" build/main.blg                                  # want 0
pdftotext build/main.pdf - | grep -n "\[?\|TODO"                     # want empty
```

The last one catches placeholder text that leaked into the rendered body, which
a clean compile will not.

To confirm every unmeasured key actually reaches the outstanding-measurements
list, compare declarations against the rendered list. Strip comments first —
`numbers.tex` documents its own API with a literal `\defTBD{key}{guess}` example,
which a naive grep counts as a real key:

```bash
python3 -c "import re,subprocess; d={k for k in re.findall(r'\\\\defTBD\{(\w+)\}', re.sub(r'(?m)^%.*$','',open('numbers.tex').read()))}; t=subprocess.run(['pdftotext','build/main.pdf','-'],capture_output=True,text=True).stdout; b=t[t.find('Outstanding measurements'):]; print('missing:', d-{k for k in d if k in b} or 'none')"
```
