# Build the paper.
#
#   make            -> main.pdf   (pdflatex + bibtex, as many passes as needed)
#   make figures    -> regenerate Figures/generated/* from build/*.jsonl
#   make teaser     -> regenerate Figures/generated/fig_teaser.pdf (needs ghostscript)
#   make watch      -> rebuild on every save
#   make clean      -> drop the LaTeX auxiliary files
#   make distclean  -> also drop main.pdf
#
# The document is pdflatex-only: main.tex sets \pdfminorversion and the class
# disables ligatures under \ifPDFTeX. Do not switch the engine to xelatex.
# Figures are committed as PDFs, so a plain `make` needs no Python and no
# ghostscript -- only a TeX installation with latexmk.

MAIN         := main
TEX          := $(MAIN).tex
PDF          := $(MAIN).pdf

LATEXMK      := latexmk
LATEXMKFLAGS := -pdf -interaction=nonstopmode -halt-on-error -file-line-error
PYTHON       ?= python3

# Everything the document reads. Touching any of it rebuilds the PDF; latexmk
# tracks the finer dependencies itself, this list only decides when to call it.
SOURCES := $(TEX) ref.bib \
           $(wildcard Sections/*.tex) \
           $(wildcard Sections_zh/*.tex) \
           $(wildcard Tables/*.tex) \
           $(wildcard Figures/*.tex) \
           $(wildcard style/*.cls) \
           $(wildcard Figures/generated/*.pdf) \
           $(wildcard Figures/cards/*.pdf) \
           assets/logo.pdf assets/plainnat.bst

.PHONY: all pdf figures teaser watch clean distclean help

all: $(PDF)
pdf: $(PDF)

$(PDF): $(SOURCES)
	@command -v $(LATEXMK) >/dev/null 2>&1 || \
	  { echo "latexmk not found -- install TeX Live/MacTeX, or run: pdflatex $(MAIN) && bibtex $(MAIN) && pdflatex $(MAIN) && pdflatex $(MAIN)"; exit 1; }
	$(LATEXMK) $(LATEXMKFLAGS) $(TEX)

# Result figures. Regenerating is optional: the PDFs they write are committed.
figures:
	$(PYTHON) scripts/make_figures.py

# The teaser goes through the card-render/ghostscript/overlay chain in
# scripts/build_teaser.sh, which needs python3, matplotlib and gs.
teaser:
	bash scripts/build_teaser.sh

watch:
	$(LATEXMK) $(LATEXMKFLAGS) -pvc $(TEX)

clean:
	$(LATEXMK) -c $(TEX)

distclean:
	$(LATEXMK) -C $(TEX)

help:
	@sed -n '3,9p' $(firstword $(MAKEFILE_LIST))
