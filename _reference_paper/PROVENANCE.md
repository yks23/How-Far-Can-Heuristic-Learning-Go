# Reference paper source

Third-party LaTeX source kept here for reference while writing this paper. It is
**not** part of our build and is deliberately excluded from version control (see
`.gitignore`) — 21 MB of figures would bloat the git history permanently and add
dead weight to the Overleaf project, where none of it is compiled.

Only this file is tracked. To restore the source:

```bash
mkdir -p _reference_paper && curl -L -o /tmp/2308.03688.tar.gz \
  https://arxiv.org/e-print/2308.03688 && tar xzf /tmp/2308.03688.tar.gz -C _reference_paper
```

## What it is

| | |
|---|---|
| Title | AgentBench: Evaluating LLMs as Agents |
| arXiv | [2308.03688](https://arxiv.org/abs/2308.03688) |
| Authors | Xiao Liu, Hao Yu, Hanchen Zhang, et al. (22 authors) |
| Submitted | 2023-08-07, last revised 2025-10-04 |
| License | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| Built with | pdfLaTeX, ICLR 2023 style (`iclr2023_conference.sty`) |

CC BY 4.0 permits redistribution with attribution, so re-publishing the source
is allowed if credited. The exclusion above is a size decision, not a licensing
one. Anything actually borrowed into our paper must still be cited.

## Layout

```
main.tex                  top-level file (per 00README.json)
0_abstract.tex            abstract
1_intro.tex               introduction
1.5_definition.tex        problem definition
2_method.tex              method
3_experiment.tex          experiments
4_related.tex             related work
5_conclusion.tex          conclusion
appendix.tex, appendix/   appendices, one file per evaluation environment
tables/                   table sources
figs/                     figures (21 MB; the demo/ screenshots dominate)
iclr2023_conference.*     conference style, bib and bst
math_commands.tex         math macros
```
