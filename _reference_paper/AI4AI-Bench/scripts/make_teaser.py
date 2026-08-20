# Figure 1 (teaser) -- the AI4AI-Bench dashboard, composited to ONE fully-vector PDF.
# Build pipeline (needs matplotlib 3.x + pdflatex + ghostscript):
#   1. python make_task_cards.py --output-dir CARDS         # ten near-square card PDFs
#   2. gs -dSubsetFonts ... CARDS/*.pdf -> cards_sq/         # subset fonts (~90 KB each)
#      gs -sDEVICE=pngalpha -r300 cards_sq/*.pdf -> cards_sq_png/   # rasters for the preview only
#   3. python make_teaser.py    # writes fig_teaser_frame.pdf (vector), a preview PNG, and teaser_compose.tex
#   4. pdflatex teaser_compose.tex (x2)   # overlays the VECTOR cards on the frame -> teaser_compose.pdf
#   5. gs -dSubsetFonts ... teaser_compose.pdf -> fig_teaser.pdf   # final subset (~950 KB, 0 raster)
import argparse
from pathlib import Path

import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle
import matplotlib.image as mpimg

matplotlib.rcParams.update({
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
    'font.family': 'DejaVu Sans',
    'axes.unicode_minus': False,
})

# ---- Einsia / Navers Lab house palette (global.css + browserBC/frontier-eng figures) ----
INK='#26313C'; BRAND='#26313C'; SUB='#6B7280'            # dark slate headings/bars, grey secondary
BLUE='#3E7CB4'                                            # muted categorical blue
CORAL='#E0863F'; GOLD='#E3A63C'; GREEN='#57A06C'; TEAL='#4E9AA6'; GREY='#AAB2BB'
LIGHTFC='#F4F6F8'; LIGHTEC='#DCE0E5'; CORALFC='#FBF2E9'; CORALEC=CORAL   # pale + warm-cream panels
HEADFC='#F1ECE3'; HEADEC='#E4DCCF'                                      # light section-header bars (warm pale)
BARBG='#EDF0F3'; BG='#FFFFFF'

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description='Build the AI4AI-Bench teaser frame and composition source.')
parser.add_argument('--card-png-dir', type=Path, default=ROOT / 'build' / 'cards_png')
parser.add_argument('--card-pdf-dir', type=Path, default=ROOT / 'Figures' / 'cards')
parser.add_argument('--output-dir', type=Path, default=ROOT / 'Figures' / 'generated')
parser.add_argument('--compose-dir', type=Path, default=ROOT / 'build' / 'teaser_compose')
args = parser.parse_args()
args.output_dir.mkdir(parents=True, exist_ok=True)
args.compose_dir.mkdir(parents=True, exist_ok=True)
CARDD=str(args.card_png_dir)
CARD_ASP=1065/960.0

# ---- canvas aspect ~2.03 so 2 rows of cards fill the right and the left column clears; isotropic units ----
W,H=169.3,83.5
fig=plt.figure(figsize=(W/12.0,H/12.0)); ax=fig.add_axes([0,0,1,1])
ax.set_xlim(0,W); ax.set_ylim(0,H); ax.axis('off')
ax.add_patch(Rectangle((0,0),W,H,fc=BG,ec='none',zorder=0))

def rrect(x,y,w,h,fc='white',ec=LIGHTEC,lw=1.1,rad=1.1,z=1):
    ax.add_patch(FancyBboxPatch((x+rad,y+rad),w-2*rad,h-2*rad,
        boxstyle='round,pad=%.3f,rounding_size=%.3f'%(rad,rad),fc=fc,ec=ec,lw=lw,zorder=z,mutation_aspect=1))
def navybar(x,y,w,h,txt,fs):
    rrect(x,y,w,h,fc=HEADFC,ec=HEADEC,lw=1.0,rad=0.9,z=2)
    ax.text(x+w/2,y+h/2,txt,ha='center',va='center',color=INK,fontsize=fs,fontweight='bold',zorder=3)
def downarr(x,y0,y1):
    ax.annotate('',xy=(x,y1),xytext=(x,y0),arrowprops=dict(arrowstyle='-|>',color='#9DB0C2',lw=1.3),zorder=3)

# ================= HEADER =================
ax.text(2.4,80.5,'AI4AI-Bench',ha='left',va='center',fontsize=23,color=BRAND,fontweight='bold',zorder=3)
ax.text(2.7,77.0,'Can coding agents improve real AI systems?',ha='left',va='center',fontsize=11,color=SUB,style='italic',zorder=3)
ax.text(167.0,80.1,'10 repositories   ·   6 systems   ·   290 configurations   ·   792 independently scored artifacts',
        ha='right',va='center',fontsize=10.0,color=INK,zorder=3)
ax.plot([2.3,167.0],[74.9,74.9],color=INK,lw=1.5,zorder=2)

# ================= SECTION BARS =================
LX0,LX1=2.3,40.6
RX0,RX1=42.0,167.4
navybar(LX0,71.9,LX1-LX0,2.5,'ONE REPRODUCIBLE LIFECYCLE',9.0)
navybar(RX0,71.9,RX1-RX0,2.5,'10 REAL AI SYSTEMS    ·    10 DISTINCT RESEARCH PROBLEMS',11.5)
BODY_TOP,BODY_BOT=71.6,9.2

# ================= LEFT: LIFECYCLE =================
BX,BW=6.4,33.6; CXN=3.6
def step(num,yc,h,title,subs,coral=False):
    fc=CORALFC if coral else LIGHTFC; ec=CORALEC if coral else LIGHTEC
    tcol=CORAL if coral else INK
    rrect(BX,yc-h/2,BW,h,fc=fc,ec=ec,lw=1.1,rad=0.85,z=2)
    ax.add_patch(Circle((CXN,yc),1.2,fc='white',ec=tcol,lw=1.35,zorder=4))
    ax.text(CXN,yc,str(num),ha='center',va='center',color=tcol,fontsize=8.0,fontweight='bold',zorder=5)
    n=1+len(subs); ls=1.5; top=yc+(n-1)*ls/2.0          # vertically centre the text block in the box
    ax.text(BX+BW/2,top,title,ha='center',va='center',color=tcol,fontsize=8.4,fontweight='bold',zorder=3)
    for i,s in enumerate(subs):
        ax.text(BX+BW/2,top-(i+1)*ls,s,ha='center',va='center',color=SUB if not coral else '#B26A44',
                fontsize=7.0,fontstyle='italic' if (coral and i==len(subs)-1) else 'normal',zorder=3)

step(1,69.75,3.3,'frozen repository',['pinned commit'])
downarr(BX+BW/2,67.9,67.2)
step(2,64.15,4.7,'agent explores',['4 h  ·  1 GPU','read · edit · train · measure'],coral=True)
downarr(BX+BW/2,61.3,60.6)
step(3,58.55,3.3,'source-only patch',['code changes only'])
ax.plot([BX,BX+BW],[55.7,55.7],color='#9DB0C2',lw=1.2,ls=(0,(4,3)),zorder=3)
ax.text(BX+BW/2,54.8,'visibility boundary',ha='center',va='center',color=BRAND,fontsize=7.5,fontweight='bold',zorder=3)
ax.text(BX+BW/2,53.4,'no weights · checkpoints · cache cross',ha='center',va='center',color=SUB,fontsize=6.7,style='italic',zorder=3)
step(4,50.35,3.9,'fresh formal replay',['12 h · 1 GPU · fixed start'],coral=True)
downarr(BX+BW/2,47.9,47.2)
step(5,45.1,3.3,'frozen evaluator',['hidden final metric'])
downarr(BX+BW/2,42.9,42.3)
rrect(BX+BW/2-6.0,39.55,12.0,2.6,fc=CORAL,ec=CORAL,lw=0,rad=0.75,z=3)
ax.text(BX+BW/2,40.85,'score',ha='center',va='center',color='white',fontsize=8.8,fontweight='bold',zorder=4)

# ================= LEFT: HEADLINE RESULTS =================
navybar(LX0,36.3,LX1-LX0,2.5,'HEADLINE RESULTS',9.0)

# A) medal standings, B) what the agents do. One bar track (BAR0..BAR1) + one value column (VALX).
BAR0,BAR1=15.0,27.6; tw=BAR1-BAR0; VALX=28.9

# A) medal score -- the only score block on the teaser. The former "share beating reference"
# bars were removed: their third bar pooled three tasks selected because agents lose on them,
# which is not a reference the paper defines.
ax.text(2.7,34.2,'A)  medal score  \u00b7  10 tasks',ha='left',va='center',fontsize=8.6,color=BRAND,fontweight='bold',zorder=3)
MED=[('Claude Opus 5',0.83,CORAL,True),('GPT-5.6 Sol',0.50,BLUE,False),('GPT-5.6 Terra',0.27,TEAL,False),
     ('Claude Sonnet 5',0.17,GOLD,False),('GPT-5.6 Luna',0.13,GREEN,False),('Kimi K3',0.00,GREY,False)]
mbh=1.55; my0=32.5; mdy=1.86
for i_,(nm,v,c,lead) in enumerate(MED):
    yb=my0-i_*mdy
    ax.text(2.7,yb,nm,ha='left',va='center',fontsize=7.2,color=INK,fontweight='bold' if lead else 'normal',zorder=3)
    rrect(BAR0,yb-mbh/2,tw,mbh,fc=BARBG,ec='none',lw=0,rad=0.4,z=2)
    if tw*v>0.3: rrect(BAR0,yb-mbh/2,tw*v,mbh,fc=c,ec='none',lw=0,rad=0.4,z=3)
    ax.text(VALX,yb,'%.2f'%v,ha='left',va='center',fontsize=8.3,color=INK,fontweight='bold' if lead else 'normal',zorder=4)
    if lead: ax.text(VALX+3.6,yb,'LEADER',ha='left',va='center',fontsize=6.1,color=CORAL,fontweight='bold',style='italic',zorder=4)
for fr in [0,0.2,0.4,0.6,0.8,1.0]:
    ax.text(BAR0+tw*fr,my0-6*mdy+0.35,'%.1f'%fr,ha='center',va='center',color=SUB,fontsize=5.8,zorder=3)

# B) what the agents do -- read from the patch census and the audited trajectories
ax.text(2.7,19.6,'B)  what the agents do',ha='left',va='center',fontsize=8.6,color=BRAND,fontweight='bold',zorder=3)
BEH=[('150/272',TEAL,  'classified patches change only how the','run is managed, not how the model learns'),
     ('\u00d726',   CORAL, 'exploration cost from lowest to highest','reasoning effort \u2014 and no gain in win rate'),
     ('2\u219218',  BLUE,  'of 30 Codex configurations attempt a','method-level change, lowest vs highest')]
by=[16.9,13.5,10.1]
for (big,c,l1,l2),yb in zip(BEH,by):
    ax.text(2.7,yb,big,ha='left',va='center',fontsize=12.2,color=c,fontweight='bold',zorder=4)
    ax.text(12.6,yb+0.78,l1,ha='left',va='center',fontsize=6.3,color=INK,zorder=4)
    ax.text(12.6,yb-0.78,l2,ha='left',va='center',fontsize=6.3,color=INK,zorder=4)

# ================= RIGHT: TASK CARD GRID (fills the area) =================
ROW1=['ddpo','digress','dpo','soup','opd']; ROW2=['openr1','npo','owl','ragen','btrm']
gx=1.2
cw=(RX1-RX0-4*gx)/5.0; chh=cw*CARD_ASP
cxs=[RX0+cw/2+i*(cw+gx) for i in range(5)]
third=((BODY_TOP-BODY_BOT)-2*chh)/3.0
r1y=BODY_TOP-third-chh/2.0; r2y=BODY_BOT+third+chh/2.0
def place(name,cx,cy):
    img=mpimg.imread('%s/fig_card_%s.png'%(CARDD,name))
    ax.imshow(img,extent=(cx-cw/2,cx+cw/2,cy-chh/2,cy+chh/2),zorder=5,interpolation='bilinear',aspect='auto')
CARDS=[(n,cx,r1y) for n,cx in zip(ROW1,cxs)]+[(n,cx,r2y) for n,cx in zip(ROW2,cxs)]

# ================= FOOTER =================
ax.plot([2.3,167.0],[8.5,8.5],color='#D6DEE6',lw=1.1,zorder=2)
ax.text(2.4,5.1,'What separates these systems is where they decide the problem lies  —  not how hard they search.',
        ha='left',va='center',fontsize=12.2,color=INK,fontweight='bold',zorder=3)
ax.text(167.0,5.1,'271 / 290 configurations scorable',ha='right',va='center',fontsize=10.5,color=INK,style='italic',zorder=3)

# 1) vector frame (no cards)
frame_pdf = args.output_dir / 'fig_teaser_frame.pdf'
preview_png = args.output_dir / 'fig_teaser.png'
fig.savefig(frame_pdf,facecolor=BG)
# 2) raster preview WITH cards
for n,cx,cy in CARDS: place(n,cx,cy)
fig.savefig(preview_png,dpi=200,facecolor=BG)
# 3) LaTeX overlay -> one fully-vector PDF
sc=12.0; pw=W/sc; ph=H/sc; cwin=cw/sc
tex=[r'\documentclass{article}',
     r'\usepackage[paperwidth=%.4fin,paperheight=%.4fin,margin=0in]{geometry}'%(pw,ph),
     r'\usepackage{tikz}',r'\usepackage{graphicx}',r'\pagestyle{empty}',
     r'\begin{document}',r'\begin{tikzpicture}[remember picture,overlay]',
     r'\node[anchor=south west,inner sep=0] at (current page.south west){\includegraphics[width=%.4fin]{\detokenize{%s}}};'%(pw,frame_pdf.as_posix())]
for n,cx,cy in CARDS:
    card_pdf=(args.card_pdf_dir / ('fig_card_%s.pdf'%n)).as_posix()
    tex.append(r'\node[anchor=center,inner sep=0] at ([xshift=%.4fin,yshift=%.4fin]current page.south west){\includegraphics[width=%.4fin]{\detokenize{%s}}};'%(cx/sc,cy/sc,cwin,card_pdf))
tex+=[r'\end{tikzpicture}%',r'\end{document}']
open(args.compose_dir/'teaser_compose.tex','w').write('\n'.join(tex))
print('done  aspect=%.3f  cw=%.2f chh=%.2f third=%.2f'%(W/H,cw,chh,third))
