# CST SAST Article Template

An A4 single-column LaTeX template with conference-paper typography for technical articles published by the
Student Association for Science and Technology of Tsinghua University's
Department of Computer Science and Technology.

## Overleaf

1. Upload the ZIP file and choose `main.tex` as the main file.
2. Compile with Overleaf's default pdfLaTeX setting.

The style also supports XeLaTeX. The packaged default is pdfLaTeX so a newly
uploaded project compiles without changing the Overleaf compiler setting.

## Local build

```bash
make
```

The generated PDF is `build/main.pdf`. Run `make clean` to remove build files.

## Authors and roles

Put role symbols after author names and declare the corresponding labels
separately. The title block lays them out in one compact, wrapping row:

```latex
\author{First Author$^{*}$, Second Author$^{\dagger\sharp}$}
\role[*]{Equal Contribution.}
\role[\dagger]{Project Lead.}
\role[\sharp]{Corresponding Authors.}
```

Delete any unused `\role` lines. Affiliation superscripts may be combined with
the role symbols in the same author marker.

## Structure

- `main.tex`: title metadata and article assembly
- `kexiearticle.sty`: typography, title block, headers, and abstract styling
- `assets/`: figures and other media

Use PDF, PNG, or JPG figures and include them with `\includegraphics`. Keep
figures legible at the template's single-column text width.

## Header marks

The original-color Tsinghua University, Department of Computer Science and
Technology, and CST SAST marks appear at the upper left by default. To use a
different set of marks, set the complete row in `main.tex`:

```latex
\setheaderlogos{%
  \kexiemark
  \headerlogosep
  \includegraphics[height=10mm]{assets/logo-a.pdf}%
  \headerlogosep
  \includegraphics[height=10mm]{assets/logo-b.pdf}%
}
```

Add or remove entries as needed. `\headerlogosep` supplies consistent spacing;
its default width is 4 mm. Keep the combined row narrow enough to leave room
for the large numeric date on the right. Dates should use the
`YYYY-MM-DD` form, for example `\articledate{2026-08-15}`.
