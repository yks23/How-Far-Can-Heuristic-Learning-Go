#!/usr/bin/env python3
"""Generate ten AI4AI-Bench task cards as vector PDFs.

Each output is 3.2 x 3.55 inches (near-square: fills the teaser grid and the
Section 2 banner). One card per task; the schematic is illustrative and the
EVAL ribbon carries the task's real final metric and direction.
"""

import argparse
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")  # measurement below needs a renderer; never a GUI window

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
from matplotlib.patches import Arc, Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle


# Einsia / Navers Lab house palette (muted categorical, warm-orange accent, slate ink)
NAVY = "#26313C"
BLUE = "#3E7CB4"
MID_BLUE = "#8FB2D6"
PALE_BLUE = "#EAF1F8"
ORANGE = "#E0863F"
PALE_ORANGE = "#FBF2E9"
GREEN = "#57A06C"
PALE_GREEN = "#EBF3ED"
RED = "#D0685C"
GRAY = "#6B7280"
MID_GRAY = "#B7BFC8"
LIGHT = "#E1E5EA"
PALE = "#F7F8FA"
WHITE = "#FFFFFF"
BLACK = "#26313C"

FIGSIZE = (3.2, 3.55)          # near-square: fills the teaser grid + §2 banner
ASP = FIGSIZE[0] / FIGSIZE[1]  # aspect correction so circles/stars stay round on [0,1]^2
TITLE_SIZE = 9
TEXT_SIZE = 8
SANS = "DejaVu Sans"
SERIF = "DejaVu Serif"
MONO = "DejaVu Sans Mono"


mpl.rcParams.update(
    {
        "font.family": SANS,
        "font.size": TEXT_SIZE,
        "axes.labelsize": TEXT_SIZE,
        "axes.titlesize": TITLE_SIZE,
        "xtick.labelsize": TEXT_SIZE,
        "ytick.labelsize": TEXT_SIZE,
        "legend.fontsize": TEXT_SIZE,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.unicode_minus": False,
        "figure.facecolor": WHITE,
        "savefig.facecolor": WHITE,
    }
)


def rounded(ax, x, y, w, h, *, fc=WHITE, ec=LIGHT, lw=0.8, radius=0.018, pad=0.004, z=1):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad={pad},rounding_size={radius}",
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z,
    )
    ax.add_patch(patch)
    return patch


def arrow(ax, start, end, *, color=NAVY, lw=1.0, dashed=False, curve=0.0, size=8,
          z=4, shrink=1.5):
    # shrink eats 3pt off every arrow, which is invisible on a 30pt one and
    # dominant on a 6pt one: ragen's 6.2pt connector rendered as 4.2pt of ink
    # sitting 1.35pt from one end and 2.61pt from the other. Pass shrink=0 on
    # short connectors so the coordinates mean what they say.
    patch = FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=size, linewidth=lw,
        color=color, linestyle="--" if dashed else "-",
        connectionstyle=f"arc3,rad={curve}", shrinkA=shrink, shrinkB=shrink, zorder=z,
    )
    ax.add_patch(patch)
    return patch


def dot(ax, x, y, r, *, fc=BLUE, ec=WHITE, lw=0.6, z=5):
    # Compensate for the 4:3 canvas so this is physically circular.
    patch = Ellipse((x, y), width=2*r, height=2*r*ASP, facecolor=fc,
                    edgecolor=ec, linewidth=lw, zorder=z)
    ax.add_patch(patch)
    return patch


def text_w(fig, s, *, size=TEXT_SIZE, family=None, weight="normal"):
    """Width of `s` in figure-fraction units, measured with the real renderer.

    Box widths used to be hand-guessed, which silently clipped the longer
    labels. Anything that has to enclose text sizes itself from this instead.
    """
    probe = fig.text(0, -1, s, fontsize=size,
                     fontfamily=family or SANS, fontweight=weight)
    renderer = fig.canvas.get_renderer()
    width = probe.get_window_extent(renderer).width
    probe.remove()
    return width / (fig.get_figwidth() * fig.dpi)


def tag(ax, text, x=0.935, y=0.795, color=GRAY):
    label = text.upper()
    w = text_w(ax.figure, label) + 0.055
    rounded(ax, x-w, y-0.033, w, 0.066, fc=WHITE, ec=LIGHT,
            lw=0.65, radius=0.02, z=6)
    ax.text(x-w/2, y, label, ha="center", va="center", color=color,
            fontsize=TEXT_SIZE, zorder=7)


def base_card(title, metric, *, accent=BLUE, note=None):
    fig = plt.figure(figsize=FIGSIZE, facecolor=WHITE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    rounded(ax, 0.02, 0.02, 0.96, 0.96, fc=WHITE, ec=LIGHT, lw=0.9,
            radius=0.035, pad=0.0, z=0)
    rounded(ax, 0.035, 0.858, 0.93, 0.105, fc=PALE_ORANGE, ec=PALE_ORANGE,
            lw=0, radius=0.025, pad=0.0, z=1)
    ax.text(0.5, 0.925, title, ha="center", va="center", color=NAVY,
            fontsize=TITLE_SIZE, fontfamily=SANS, fontweight="bold", zorder=8)

    # Consistent evaluation ribbon, readable at thumbnail size.
    rounded(ax, 0.055, 0.055, 0.89, 0.12, fc=PALE, ec=LIGHT,
            lw=0.75, radius=0.025, z=2)
    rounded(ax, 0.07, 0.075, 0.17, 0.08, fc=accent, ec=accent,
            lw=0, radius=0.02, z=3)
    ax.text(0.155, 0.115, "EVAL", ha="center", va="center", color=WHITE,
            fontfamily=SANS, fontweight="bold", fontsize=TEXT_SIZE, zorder=4)
    ax.text(0.265, 0.115, metric, ha="left", va="center", color=NAVY,
            fontsize=TEXT_SIZE, linespacing=1.0, zorder=4)
    # task-type badges (schematic / synthetic / illustrative) intentionally omitted
    # for a cleaner task-suite figure; `note` is accepted but not drawn.
    _ = note
    return fig, ax


def save(fig, out_dir: Path, name: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"fig_card_{name}.pdf"
    fig.savefig(path, format="pdf", dpi=300, bbox_inches=None, pad_inches=0,
                metadata={"Creator": "Matplotlib"})
    plt.close(fig)
    return path


def abstract_image(ax, x, y, w, h):
    rounded(ax, x, y, w, h, fc=PALE, ec=MID_BLUE, lw=0.9, radius=0.018, z=2)
    ax.add_patch(Polygon([[x+.02*w,y+.12*h],[x+.36*w,y+.54*h],
                          [x+.55*w,y+.32*h],[x+.78*w,y+.67*h],[x+.98*w,y+.16*h]],
                         closed=True, facecolor=MID_BLUE, edgecolor="none",
                         alpha=0.55, zorder=3))
    ax.add_patch(Polygon([[x+.02*w,y+.12*h],[x+.26*w,y+.32*h],
                          [x+.48*w,y+.16*h],[x+.70*w,y+.40*h],[x+.98*w,y+.16*h]],
                         closed=True, facecolor=ORANGE, edgecolor="none",
                         alpha=0.72, zorder=4))
    dot(ax, x+.22*w, y+.72*h, .027*w, fc=GREEN, ec=GREEN, z=5)


def card_ddpo(out_dir: Path):
    fig, ax = base_card("DDPO: Aesthetic Alignment",
                        "LAION aesthetic ↑\nmean of 256 images",
                        accent=BLUE, note="schematic")
    abstract_image(ax, .070, .305, .26, .36)
    ax.text(.20, .700, "SD 1.5", ha="center", va="center", color=NAVY, fontweight="bold")
    arrow(ax, (.345,.475), (.455,.475), color=NAVY)
    dot(ax, .555, .475, .080, fc=PALE_ORANGE, ec=ORANGE, lw=1.0, z=2)
    star = []
    for i in range(10):
        angle = np.pi/2 + i*np.pi/5
        radius = .044 if i%2 == 0 else .020
        star.append((.555+radius*np.cos(angle), .475+radius*ASP*np.sin(angle)))
    ax.add_patch(Polygon(star, closed=True, facecolor=ORANGE, edgecolor=WHITE,
                         linewidth=.5, zorder=5))
    ax.text(.555, .315, "aesthetic scorer", ha="center", va="center", color=NAVY)
    arrow(ax, (.655,.475), (.735,.475), color=NAVY)
    x0, x1, yy = .75, .925, .455
    ax.plot([x0,x1], [yy,yy], color=NAVY, lw=1.1, zorder=3)
    for i in range(6):
        xx = x0+(x1-x0)*i/5
        ax.plot([xx,xx], [yy-.025,yy+.025], color=NAVY, lw=.7, zorder=3)
    # Needle sits at the shipped final score, 5.53 / 10 (instruction.md).
    px = x0+.553*(x1-x0)
    ax.add_patch(Polygon([[px,yy+.025],[px-.016,yy+.075],[px+.016,yy+.075]],
                         facecolor=GREEN, edgecolor="none", zorder=4))
    ax.text(x0, yy-.06, "0", ha="center", va="top")
    ax.text(x1, yy-.06, "10", ha="center", va="top")
    ax.text((x0+x1)/2, .615, "score", ha="center", va="center", color=NAVY, fontweight="bold")
    arrow(ax, (.58,.625), (.27,.655), color=ORANGE, lw=1.0, dashed=True, curve=.25, size=7)
    # Clear of the arc's crown: at .710 the dashes cut the descender of "update".
    ax.text(.43, .748, "RL update", ha="center", va="center", color=ORANGE)
    return save(fig, out_dir, "ddpo")


MOL_EDGES = [
    [(0,1),(1,2),(2,3),(3,4),(4,0),(2,5)],          # 5-ring + branch
    [(0,1),(1,2),(2,3),(3,4),(4,5),(5,0),(1,6)],    # 6-ring + branch
    # 6-ring bridged across the middle. The old 4-ring + 2-chain drew three
    # crossing bonds and merged two atoms, which reads as a drawing error.
    [(0,1),(1,2),(2,3),(3,4),(4,5),(5,0),(2,5)],
]


def molecule_axes(fig, box, variant):
    m = fig.add_axes(box)
    m.set_xlim(-1.2,1.2); m.set_ylim(-1,1); m.set_aspect("equal"); m.axis("off")
    n = 7 if variant%3 == 1 else 6
    angles = np.linspace(0,2*np.pi,n,endpoint=False)+.18*variant
    pts = np.c_[.68*np.cos(angles), .56*np.sin(angles)]
    # Branch offsets kept short enough that no node, including its white stroke,
    # crosses the sub-axes limits; the old .34/.36 clipped variant 4's top atom.
    if variant%3 == 0:
        pts[5] = pts[2]+[.58, .30 if variant%2 == 0 else -.30]
    elif variant%3 == 1:
        pts[6] = pts[1]+[.50,.26]
    for a,b in MOL_EDGES[variant%3]:
        m.plot([pts[a,0],pts[b,0]],[pts[a,1],pts[b,1]],color=GRAY,lw=1.0,zorder=1)
    # Fixed per-position atom types so the colours mean what the legend says.
    for i,(xx,yy) in enumerate(pts):
        m.add_patch(Ellipse((xx,yy),.24,.24,facecolor=ATOM_COLORS[i%len(ATOM_COLORS)],
                            edgecolor=WHITE,linewidth=.6,zorder=2))


# QM9 heavy atoms, in the conventional CPK-like scheme used by the legend.
ATOM_COLORS = [GRAY,BLUE,GRAY,RED,GRAY,GRAY,BLUE]


def card_digress(out_dir: Path):
    fig, ax = base_card("DiGress: Molecular Generation",
                        "upstream test NLL ↓\nreal QM9 test split",
                        accent=BLUE, note="schematic")
    rng = np.random.RandomState(4)
    for _ in range(12):
        dot(ax,.09+.16*rng.rand(),.31+.40*rng.rand(),.008,
            fc=MID_BLUE,ec=WHITE,lw=.3,z=2)
    for _ in range(11):
        x1,y1=.09+.16*rng.rand(),.31+.40*rng.rand()
        x2,y2=.09+.16*rng.rand(),.31+.40*rng.rand()
        ax.plot([x1,x2],[y1,y2],color=MID_BLUE,lw=.55,alpha=.35,zorder=1)
    ax.text(.17,.745,"noise",ha="center",va="center",color=GRAY)
    # Solid navy like every other forward-flow arrow in the deck; dashed orange
    # is reserved for feedback/trajectory edges.
    arrow(ax,(.262,.51),(.340,.51),color=NAVY)
    xs=[.35,.545,.74]; ys=[.49,.255]
    for row,y in enumerate(ys):
        for col,x in enumerate(xs):
            molecule_axes(fig,[x,y,.18,.20],row*3+col)
    ax.text(.64,.725,"generated molecules",ha="center",va="center",color=NAVY,fontweight="bold")
    # The 10,000 belongs to the sampled set, not to the NLL's evaluation set.
    for i,(color,label) in enumerate(((GRAY,"C"),(BLUE,"N"),(RED,"O"))):
        cx=.395+i*.070
        dot(ax,cx,.225,.011,fc=color,ec=WHITE,lw=.4,z=3)
        ax.text(cx+.020,.225,label,ha="left",va="center",color=NAVY)
    ax.text(.930,.225,"10,000 sampled",ha="right",va="center",color=GRAY)
    return save(fig,out_dir,"digress")


def response_card(ax,x,y,w,h,label,text,color,symbol):
    rounded(ax,x,y,w,h,fc=WHITE,ec=color,lw=.9,radius=.018,z=2)
    # Text-driven: the fixed .25 was sized for the longer of the two labels and
    # still let "✓  strict pass" out by 0.08pt on both sides.
    lab=f"{symbol}  {label}"
    lw_=text_w(ax.figure,lab,weight="bold")+.038
    rounded(ax,x+.012,y+h-.085,lw_,.065,fc=color,ec=color,lw=0,radius=.016,z=3)
    ax.text(x+.012+lw_/2,y+h-.052,lab,ha="center",va="center",
            color=WHITE,fontweight="bold",zorder=4)
    ax.text(x+.022,y+h-.105,text,ha="left",va="top",color=BLACK,
            fontfamily=MONO,linespacing=1.15,zorder=4)


def card_dpo(out_dir: Path):
    fig,ax=base_card("DPO: Instruction Following",
                     "IFEval prompt-level strict ↑\n413 final prompts (285 unseen)",
                     accent=GREEN,note="synthetic")
    rounded(ax,.065,.25,.34,.48,fc=PALE,ec=MID_BLUE,lw=.9,radius=.025,z=2)
    ax.text(.09,.690,"PROMPT",ha="left",va="center",color=BLUE,fontfamily=SERIF,fontweight="bold")
    # Top-anchored: centring this block let its first line ride up into PROMPT.
    ax.text(.09,.648,"List exactly\nthree fruits.\nDo not use\ncommas.",ha="left",va="top",
            color=BLACK,fontfamily=MONO,linespacing=1.15)
    ax.plot([.09,.38],[.428,.428],color=LIGHT,lw=.7,zorder=3)
    # Stacked, self-describing, and on WHITE: the old side-by-side "3" / "no ,"
    # chips were PALE_BLUE on the box's PALE, a 13/7/1 RGB step that rendered as
    # bare floating text at 900 dpi, and neither label said what it constrained.
    for i,txt in enumerate(["count = 3","no commas"]):
        w=text_w(fig,txt,weight="bold")+.045
        yy=.378-i*.075
        rounded(ax,.095,yy-.032,w,.064,fc=WHITE,ec=BLUE,lw=.75,radius=.018,z=3)
        ax.text(.095+w/2,yy,txt,ha="center",va="center",color=BLUE,
                fontweight="bold",zorder=4)
    arrow(ax,(.415,.52),(.49,.52),color=NAVY)
    # One line each: the two-line answers pushed "cherry" onto the card border.
    response_card(ax,.505,.560,.425,.175,"strict pass","apple / pear / fig",GREEN,"✓")
    response_card(ax,.505,.335,.425,.175,"strict fail","apple, pear, fig",ORANGE,"×")
    ax.text(.915,.290,"commas used",ha="right",va="center",color=ORANGE)
    return save(fig,out_dir,"dpo")


def card_btrm(out_dir: Path):
    fig,ax=base_card("BTRM: Reward Modeling",
                     "RewardBench v1 score ↑\n4-section mean, n = 2,985",
                     accent=ORANGE,note="synthetic")
    rounded(ax,.075,.70,.44,.09,fc=PALE_BLUE,ec=MID_BLUE,lw=.7,radius=.02)
    ax.text(.095,.745,"Why is the sky blue?",ha="left",va="center",fontfamily=MONO)
    rounded(ax,.065,.405,.45,.245,fc=PALE_GREEN,ec=GREEN,lw=.8,radius=.018)
    ax.plot([.08,.08],[.425,.63],color=GREEN,lw=3)
    ax.text(.095,.615,"chosen",ha="left",va="center",color=GREEN,fontweight="bold")
    ax.text(.095,.51,"Sunlight scatters\noff air molecules;\nblue wavelengths\nscatter most.",
            ha="left",va="center",fontfamily=MONO,linespacing=.95)
    rounded(ax,.065,.215,.45,.155,fc=PALE_ORANGE,ec=ORANGE,lw=.8,radius=.018)
    ax.plot([.08,.08],[.240,.35],color=ORANGE,lw=3)
    ax.text(.095,.335,"rejected",ha="left",va="center",color=ORANGE,fontweight="bold")
    # Was .275 in a box floored at .225, leaving the second line 0.62pt off the
    # border; the chosen box above gives its last line 3.4pt.
    ax.text(.095,.281,"Because it\nreflects the ocean.",ha="left",va="center",fontfamily=MONO,linespacing=1.0)
    arrow(ax,(.52,.53),(.655,.50),color=GREEN); arrow(ax,(.52,.295),(.655,.43),color=ORANGE)
    dot(ax,.74,.50,.074,fc=PALE_BLUE,ec=BLUE,lw=1.0,z=2)
    # Beam, needle, base, hangers, pans. The old glyph hung the pans on splayed
    # arms that put their tips at 1.012 of the rim radius, so pan and rim strokes
    # merged, and ran the needle .06 above the beam, which read as a stray tail.
    ax.plot([.712,.768],[.525,.525],color=NAVY,lw=1.0,zorder=4)
    ax.plot([.74,.74],[.465,.548],color=NAVY,lw=1.0,zorder=4)
    ax.plot([.722,.758],[.465,.465],color=NAVY,lw=1.0,zorder=4)
    ax.plot([.712,.712],[.525,.492],color=NAVY,lw=.8,zorder=4)
    ax.plot([.768,.768],[.525,.492],color=NAVY,lw=.8,zorder=4)
    ax.add_patch(Arc((.712,.492),.042,.034,theta1=180,theta2=360,color=GREEN,lw=1.0,zorder=4))
    ax.add_patch(Arc((.768,.492),.042,.034,theta1=180,theta2=360,color=ORANGE,lw=1.0,zorder=4))
    ax.text(.74,.665,"reward model",ha="center",va="center",color=NAVY,fontweight="bold")
    ax.text(.74,.295,"r(chosen) > r(rejected)",ha="center",va="center",fontfamily=SANS)
    return save(fig,out_dir,"btrm")


def sample_grid(ax,x,y,cols=8,rows=4,correct=None,scale=1.0):
    correct=correct or set(); w,h,gap=.027*scale,.036*scale,.005*scale
    for r in range(rows):
        for c in range(cols):
            idx=r*cols+c
            ax.add_patch(Rectangle((x+c*(w+gap),y+(rows-1-r)*(h+gap)),w,h,
                                   facecolor=BLUE if idx in correct else WHITE,
                                   edgecolor=BLUE if idx in correct else MID_BLUE,
                                   linewidth=.55,zorder=3))


def card_opd(out_dir: Path):
    fig,ax=base_card("OPD: Math Distillation",
                     "AIME24+25 mean acc ↑\n32 samples × 60 problems",
                     accent=BLUE,note="synthetic")
    rounded(ax,.055,.31,.355,.40,fc=PALE,ec=MID_BLUE,lw=.8,radius=.02)
    # 124^2 = 15376, and no smaller positive integer squares to ...376.
    ax.text(.075,.665,"Find smallest\nN > 0 with N²\nending in 376.",
            ha="left",va="top",fontfamily=MONO,linespacing=1.18)
    ax.plot([.075,.39],[.44,.44],color=LIGHT,lw=.7)
    ax.text(.075,.385,"Answer: 124",ha="left",va="center",color=BLUE,fontfamily=MONO,fontweight="bold")
    arrow(ax,(.42,.51),(.49,.51),color=NAVY)
    dot(ax,.57,.51,.070,fc=PALE_BLUE,ec=BLUE,lw=1.0,z=2)
    # "student" outside the circle: inside, its first and last letters sat on the stroke.
    ax.text(.57,.645,"student",ha="center",va="center",color=NAVY,fontweight="bold")
    ax.text(.57,.51,"1.5B",ha="center",va="center",color=BLUE,fontweight="bold")
    arrow(ax,(.65,.51),(.695,.51),color=NAVY)
    sample_grid(ax,.70,.405,correct={0,1,3,4,6,7,9,10,11,14,16,17,19,20,22,24,25,28,30},scale=.9)
    ax.text(.815,.68,"32 rollouts",ha="center",va="center",color=NAVY,fontweight="bold")
    arrow(ax,(.845,.37),(.61,.37),color=ORANGE,dashed=True,curve=-.22,size=7)
    ax.text(.74,.29,"on-policy feedback",ha="center",va="center",color=ORANGE)
    return save(fig,out_dir,"opd")


def code_window(ax,x,y,w,h):
    rounded(ax,x,y,w,h,fc=PALE,ec=MID_BLUE,lw=.9,radius=.02)
    ax.add_patch(Rectangle((x,y+h-.075),w,.075,facecolor=PALE_BLUE,edgecolor="none",zorder=2))
    for i,color in enumerate([RED,ORANGE,GREEN]):
        dot(ax,x+.028+i*.031,y+h-.038,.008,fc=color,ec=color,lw=0,z=4)
    # Indents balanced against the right edge: at .040 the wrapped line left a
    # 2.93pt gap to the border against a 10.14pt left inset, which reads as
    # running into it. PEP8 would align the continuation under "sum(" at ~.30,
    # which does not fit, so the hanging indent stays proportional instead.
    lines=[("def solve(xs):",.020),("return sum(x for x in xs",.028),("if x % 2 == 0)",.080)]
    for i,(line,offset) in enumerate(lines):
        ax.text(x+offset,y+h-.13-i*.075,line,ha="left",va="center",fontfamily=MONO)


def card_openr1(out_dir: Path):
    fig,ax=base_card("OpenR1: Code SFT",
                     "LiveCodeBench v6 pass@1 ↑\n128 problems (hash order)",
                     accent=GREEN,note="synthetic")
    ax.text(.075,.755,"Given a list of ints,\nreturn the sum of all even numbers.",
            ha="left",va="center",fontfamily=MONO,linespacing=1.15)
    code_window(ax,.06,.27,.56,.36)
    arrow(ax,(.628,.47),(.655,.47),color=NAVY)
    dot(ax,.71,.47,.056,fc=PALE_BLUE,ec=BLUE,lw=1.0,z=2)
    ax.text(.71,.47,"SFT",ha="center",va="center",color=BLUE,fontweight="bold")
    arrow(ax,(.77,.47),(.795,.47),color=NAVY)
    for i,yy in enumerate([.59,.49,.39]):
        rounded(ax,.80,yy-.045,.13,.09,fc=WHITE,ec=GREEN if i<2 else MID_BLUE,
                lw=.75,radius=.015)
        ax.text(.825,yy,"✓" if i<2 else "…",ha="center",va="center",
                color=GREEN if i<2 else BLUE,fontweight="bold")
        ax.plot([.85,.905],[yy,yy],color=LIGHT,lw=1.4)
    # Last hardcoded chip width in the deck: "pass@1" cleared it by 0.39pt left
    # and 0.62pt right, so the fill read as a tight outline around the glyphs.
    pw=text_w(fig,"pass@1",weight="bold")+.040
    rounded(ax,.862-pw/2,.255,pw,.075,fc=PALE_GREEN,ec=GREEN,lw=.8,radius=.02)
    ax.text(.862,.293,"pass@1",ha="center",va="center",color=GREEN,fontweight="bold")
    return save(fig,out_dir,"openr1")


def card_npo(out_dir: Path):
    fig,_=base_card("NPO: Machine Unlearning",
                    "extraction ↓ / model utility ↑\ndominance on both, never combined",
                    accent=ORANGE,note=None)
    ax=fig.add_axes([.18,.33,.68,.42])
    ax.set_xlim(0,.8); ax.set_ylim(.4,.65)
    ax.set_xlabel("extraction strength  (↓ better)",labelpad=2)
    ax.set_ylabel("model utility  (↑ better)",labelpad=3)
    ax.set_xticks([0,.4,.8]); ax.set_yticks([.4,.5,.6])
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.tick_params(direction="out",length=3)
    ax.add_patch(Rectangle((0,.57),.20,.08,facecolor=PALE_GREEN,edgecolor="none",zorder=0))
    ax.text(.225,.625,"target region",ha="left",va="center",color=GREEN)
    start=(.708,.597); recipe=(.063,.479)
    ax.scatter(*start,s=48,color=GRAY,edgecolor=WHITE,linewidth=.6,zorder=4)
    ax.scatter(*recipe,s=54,color=BLUE,edgecolor=WHITE,linewidth=.6,zorder=4)
    ax.annotate("",xy=recipe,xytext=start,
                arrowprops=dict(arrowstyle="-|>",color=ORANGE,lw=1.15,linestyle="--",mutation_scale=8))
    ax.annotate("start",xy=start,xytext=(-3,6),textcoords="offset points",ha="right",va="bottom")
    ax.annotate("recipe",xy=recipe,xytext=(5,-2),textcoords="offset points",ha="left",va="top",color=BLUE)
    # Below the trajectory, unmasked: the white bbox punched a gap in the arrow
    # wide enough to read as a broken line. Pushed right and tightened to single
    # spaces because at .471 its left edge sat 3.48pt from "recipe" with 5.45pt
    # of vertical overlap -- under an 8pt word space of ~2.2pt, so pymupdf and a
    # reader both ran the two together as "recipe forgetting ↑ · utility ↓".
    ax.text(.50,.445,"forgetting ↑ · utility ↓",ha="center",va="center",color=ORANGE)
    return save(fig,out_dir,"npo")


def card_owl(out_dir: Path):
    fig,ax0=base_card("OWL: Layer-Adaptive Pruning",
                      "WikiText-2 test PPL ↓\n70% overall sparsity",
                      accent=BLUE,note=None)
    # Text-driven: at a hardcoded .255 the "dense*" chip cleared its label by
    # 0.64pt, so the fill read as an outline traced round the glyphs.
    d_lab,s_lab="dense* 10.86","sparse  53.36"
    dw=text_w(fig,d_lab,weight="bold")+.036
    sw=text_w(fig,s_lab,weight="bold")+.036
    d_x,s_x=.07,.07+dw+.045
    rounded(ax0,d_x,.70,dw,.09,fc=PALE_BLUE,ec=MID_BLUE,lw=.7,radius=.02)
    rounded(ax0,s_x,.70,sw,.09,fc=PALE_ORANGE,ec=ORANGE,lw=.7,radius=.02)
    ax0.text(d_x+dw/2,.745,d_lab,ha="center",va="center",color=NAVY,fontweight="bold")
    ax0.text(s_x+sw/2,.745,s_lab,ha="center",va="center",color=ORANGE,fontweight="bold")
    arrow(ax0,(d_x+dw+.008,.745),(d_x+dw+.037,.745),color=NAVY,size=7)
    # Anchored to the chip, not a fixed .68: sizing the chips from their text
    # pushed the sparse one to .727, straight through this label.
    ax0.text(s_x+sw+.025,.745,"repo ref.",ha="left",va="center",color=GRAY)
    # Trimmed: the longer wording left 2.93pt to the card frame, and 8.0pt is
    # already the deck's font floor, so the string had to give instead.
    ax0.text(.07,.655,"*dense fails the 70% gate; sparse = 3-seed mean",
             ha="left",va="center",color=GRAY)
    ax=fig.add_axes([.16,.325,.76,.275])
    layers=np.arange(1,33)
    vals=np.array([.58,.57,.59,.61,.64,.68,.72,.76,.79,.81,.82,.81,.79,.77,.75,.73,
                   .71,.69,.68,.69,.71,.73,.76,.78,.77,.75,.73,.70,.67,.64,.61,.59])
    vals += .70-vals.mean()
    ax.bar(layers,vals,width=.78,color=BLUE,edgecolor="none")
    ax.axhline(.70,color=ORANGE,lw=1.0,ls="--")
    # Lifted clear of the bars into the empty top band. Sitting on the gate line
    # at y=.715, its white knockout box erased 8.71pt off the tops of layers
    # 22-27 -- the profile's second hump -- leaving a flat plateau on the 0.70
    # line that the data does not contain. Colour ties it to the dashed line.
    ax.text(32.4,.815,"uniform 70%",ha="right",va="bottom",color=ORANGE,
            bbox=dict(facecolor=WHITE,edgecolor="none",pad=1.2))
    ax.text(1.0,.885,"schematic profile",ha="left",va="top",color=GRAY)
    ax.set_xlim(.2,32.8); ax.set_ylim(.5,.9)
    ax.set_xlabel("layer index",labelpad=2); ax.set_ylabel("sparsity",labelpad=2)
    ax.set_xticks([1,8,16,24,32]); ax.set_yticks([.5,.7,.9])
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.tick_params(direction="out",length=3)
    return save(fig,out_dir,"owl")


def card_soup(out_dir: Path):
    fig,ax0=base_card("Model Soup: Weight Averaging",
                      "ImageNet-V2 top-1 ↑\nall 10,000 images",
                      accent=GREEN,note="illustrative")
    ax=fig.add_axes([.15,.34,.45,.39])
    rng=np.random.RandomState(11); xs=np.arange(1,73)
    ys=67.3+.7*np.sin(xs/7.2)+rng.normal(0,.52,len(xs))
    best_i=int(np.argmax(ys)); best=float(ys[best_i])
    # Repo ordering: uniform (0.6859) sits *below* best_single (0.6874), a -0.0015
    # statistical tie. strict_greedy has no final score in the repo, so it is not drawn.
    uniform=best-.15
    ax.scatter(xs,ys,s=13,color=LIGHT,edgecolors=GRAY,linewidths=.28,zorder=1)
    ax.axhline(uniform,color=BLUE,lw=1.0,ls="--",zorder=3)
    # The y-axis is deliberately unlabelled, so the drop from the triangle to this
    # line is the reader's only cue and it reads as a demonstrated regression.
    # instruction.md is explicit that -0.0015 is ~0.56 paired standard errors and
    # "should be described as a statistical tie, not a demonstrated regression".
    # Annotated on the line, not flattened onto it: best_single really is the
    # higher number, and hiding that would be its own error. Placed like owl's
    # "uniform 70%" -- the deck already labels a gate line this way.
    ax.text(73,uniform+.06,"gap 0.56 SE: tie",ha="right",va="bottom",color=GRAY,
            bbox=dict(facecolor=WHITE,edgecolor="none",pad=1.2))
    ax.scatter(xs[best_i],best,s=58,marker="^",color=ORANGE,edgecolors=WHITE,linewidths=.6,zorder=4)
    ax.set_xlim(0,74); ax.set_ylim(65.8,best+.55)
    ax.set_xlabel("ingredient index",labelpad=2); ax.set_ylabel("top-1 accuracy",labelpad=3)
    ax.set_xticks([1,24,48,72]); ax.set_yticks([])
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.tick_params(direction="out",length=3)
    for i,(name,color,marker) in enumerate((("best_single",ORANGE,"^"),("uniform",BLUE,None))):
        yy=.545-i*.13
        rounded(ax0,.63,yy-.045,.31,.09,fc=WHITE,ec=color,lw=.75,radius=.018)
        if marker:
            ax0.scatter([.665],[yy],s=32,marker=marker,color=color,zorder=5)
        else:
            ax0.plot([.645,.685],[yy,yy],color=color,lw=1.0,ls="--",zorder=5)
        ax0.text(.700,yy,name,ha="left",va="center",color=NAVY)
    return save(fig,out_dir,"soup")


def card_ragen(out_dir: Path):
    fig,ax=base_card("RAGEN: Sokoban GRPO",
                     "held-out solve rate ↑\n512 boards",
                     accent=GREEN,note="illustrative")
    board=fig.add_axes([.07,.235,.53,.56])
    board.set_xlim(0,6); board.set_ylim(0,6); board.set_aspect("equal"); board.axis("off")
    walls={(r,c) for r in range(6) for c in range(6) if r in {0,5} or c in {0,5}}
    walls|={(1,2),(1,3),(4,3)}
    for r in range(6):
        for c in range(6):
            wall=(r,c) in walls
            board.add_patch(Rectangle((c,5-r),1,1,facecolor=NAVY if wall else PALE_BLUE,
                                      edgecolor=WHITE,linewidth=.9))
    board.add_patch(Ellipse((4.5,2.5),.53,.53,facecolor=WHITE,edgecolor=GREEN,linewidth=1.7,zorder=4))
    board.add_patch(Ellipse((4.5,2.5),.10,.10,facecolor=GREEN,edgecolor="none",zorder=5))
    board.add_patch(Rectangle((2.18,2.18),.64,.64,facecolor=ORANGE,edgecolor=NAVY,linewidth=.8,zorder=4))
    board.add_patch(Rectangle((2.27,2.54),.46,.13,facecolor="#F3B38F",edgecolor="none",zorder=5))
    board.add_patch(Ellipse((1.5,2.5),.58,.58,facecolor=BLUE,edgecolor=WHITE,linewidth=.8,zorder=4))
    board.plot([2.95,3.45,3.95],[2.5,2.5,2.5],color=ORANGE,lw=1.1,ls="--",zorder=3)
    board.add_patch(FancyArrowPatch((3.95,2.5),(4.2,2.5),arrowstyle="-|>",mutation_scale=8,color=ORANGE,lw=1.0,zorder=4))
    # Right-hand group on an explicit horizontal budget. From the board's cells
    # (x=125.6pt) to 3pt inside the frame there are 97.4pt. The old ring was
    # 50.7pt and the solved box is 41.4pt, which left 5.3pt for TWO connectors --
    # so neither could reach what it connected and both floated in white space.
    # Shrinking the ring to 42.6pt buys 13.4pt, i.e. ~6.5pt each, which is the
    # deck's own floor (openr1's connectors are 5.8 and 6.2pt).
    # CY=.468 is the centre of the board's action row (agent, box, target) at
    # y=91.9pt, so the connector leaves the board on the row it just solved
    # instead of the empty row above it. Ring and box share this centreline; they
    # never did before, which is why the old connector had to run diagonally.
    CX,CY=.6757,.468
    RX,RY=.185,.2353            # ring; same 4.5% ovality as the original .22/.28
    dot(ax,CX,CY,.070,fc=PALE_ORANGE,ec=ORANGE,lw=1.0,z=2)
    ax.text(CX,CY,"GRPO",ha="center",va="center",color=ORANGE,fontweight="bold")
    # The head goes at the arc's own terminal end, on the ccw tangent there, so the
    # ring's gap is where the arrow starts and stops -- that is what makes it read as
    # a cycle. Two earlier versions put it mid-arc (once at 30 deg aimed 0 deg, which
    # was 59 deg off the tangent and pointed into the annulus at nothing; then at the
    # top aimed left, on-tangent but detached from the gap, so it read as a broken
    # ring with a head stuck on it). Derived from RX/RY/THEAD rather than typed in,
    # because every hardcoded version of this drifted off the curve.
    THEAD = 302.0
    ax.add_patch(Arc((CX,CY),RX,RY,theta1=30,theta2=294,color=ORANGE,lw=1.0,zorder=3))
    t = np.radians(THEAD)
    ex, ey = CX + RX/2*np.cos(t), CY + RY/2*np.sin(t)      # arc point, fig fractions
    # ccw tangent of x=a cos t, y=b sin t is (-a sin t, b cos t); undo the 4:3 canvas
    # so the head is aimed along the physically visible direction, not the stretched one.
    tx, ty = -RX/2*np.sin(t), RY/2*np.cos(t)*(1/ASP)
    L = np.hypot(tx, ty); tx, ty = tx/L, ty/L
    # Sized to the deck, not to the ring: every arrowhead in the ten cards is
    # 3.2x3.2pt and the two existing loop heads (ddpo, opd) are 3.12x2.58. The first
    # version of this one was 4.72x4.06, the largest head in the deck by 47%.
    HL, HW = .0126, .0069                                  # bbox lands at ~3.3x2.8pt
    ax.add_patch(Polygon([[ex+tx*HL*.62, ey+ty*HL*.62*ASP],
                          [ex-tx*HL*.38-ty*HW, ey+(-ty*HL*.38+tx*HW)*ASP],
                          [ex-tx*HL*.38+ty*HW, ey+(-ty*HL*.38-tx*HW)*ASP]],
                         facecolor=ORANGE,edgecolor="none",zorder=4))
    # Both connectors horizontal at the ring's centre height, which is the deck's
    # idiom: 8 of its 10 arrows are horizontal, and the only diagonals (btrm) join
    # boxes that are genuinely offset. Each has 8.91pt of white to live in and gets
    # 1.3pt of clearance at both ends, measured off the render as INK, not as
    # coordinates: "-|>" pulls its tip back 1.11pt from the endpoint (head length at
    # mutation_scale=8) and the 1.0pt stroke then adds 0.5pt of cap at each extreme.
    # Endpoints below are therefore ink_target -/+ those two corrections.
    arrow(ax,(.5504,CY),(.5788,CY),color=NAVY,shrink=0)   # ink 126.31-132.63
    sw=text_w(fig,"solved",weight="bold")+.0434
    s_x0=.9624-sw
    arrow(ax,(.7550,CY),(s_x0-.0075,CY),color=NAVY,shrink=0)   # ink 173.47-179.79
    rounded(ax,s_x0,CY-.10,sw,.20,fc=PALE_GREEN,ec=GREEN,lw=.9,radius=.02)
    ax.text(s_x0+sw/2,CY+.030,"✓",ha="center",va="center",color=GREEN,fontsize=12,fontweight="bold")
    ax.text(s_x0+sw/2,CY-.050,"solved",ha="center",va="center",color=GREEN,fontweight="bold")
    return save(fig,out_dir,"ragen")


GENERATORS = {
    "ddpo": card_ddpo,
    "digress": card_digress,
    "dpo": card_dpo,
    "btrm": card_btrm,
    "opd": card_opd,
    "openr1": card_openr1,
    "npo": card_npo,
    "owl": card_owl,
    "soup": card_soup,
    "ragen": card_ragen,
}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir",type=Path,default=Path(__file__).resolve().parent/"pdf")
    parser.add_argument("--only",choices=sorted(GENERATORS),nargs="*",help="Generate selected cards")
    args=parser.parse_args()
    for name in (args.only or list(GENERATORS)):
        print(GENERATORS[name](args.output_dir))


if __name__ == "__main__":
    main()
