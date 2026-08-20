import argparse
import json
import statistics
from pathlib import Path

import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, numpy as np
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description='Generate the six analysis figures used by AI4AI-Bench.')
parser.add_argument('--data-dir', type=Path, default=ROOT / 'build')
parser.add_argument('--output-dir', type=Path, default=ROOT / 'Figures' / 'generated')
args = parser.parse_args()
args.output_dir.mkdir(parents=True, exist_ok=True)

D=args.data_dir; OUT=args.output_dir
ds=json.load(open(D/'frozen_dataset.json')); dg=json.load(open(D/'results_digest.json')); mr=json.load(open(D/'medal_rank.json'))
tasks=ds['tasks']; configs=ds['configs']
npodom=json.load(open(D/'npo_dominance.json'))['cells']

# Shared Einsia paper palette, derived from Frontier-Eng and BrowserBC.
INK='#26313C'; SUB='#6B7280'; GRID='#E1E5EA'; EDGE='#C8CED5'
BLUE='#3E7CB4'; MID_BLUE='#8FB2D6'; PALE_BLUE='#EAF1F8'
ORANGE='#E0863F'; PALE_ORANGE='#FBF2E9'; GOLD='#E3A63C'
GREEN='#57A06C'; TEAL='#4E9AA6'; RED='#D0685C'; GREY='#AAB2BB'
LIGHT='#EDF0F3'; PALE='#F7F8FA'; WHITE='#FFFFFF'; WARM='#F1ECE3'
# Historical names retained below to keep the data/plot code compact.
CORAL=ORANGE; NAVY=BLUE; SAGE=GREEN
plt.rcParams.update({'pdf.fonttype':42,'ps.fonttype':42,'font.family':'sans-serif','font.size':10,
 'text.color':INK,'axes.labelcolor':INK,'axes.edgecolor':EDGE,'xtick.color':INK,'ytick.color':INK,
 'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.color':GRID,'grid.linewidth':0.65,
 'axes.axisbelow':True,'axes.linewidth':0.8,'figure.dpi':150,'figure.facecolor':WHITE,'axes.facecolor':WHITE,
 'legend.frameon':False,'xtick.major.size':0,'ytick.major.size':0})
MCOL={'claude-opus-5':CORAL,'claude-sonnet-5':GOLD,'gpt-5.6-sol':NAVY,'gpt-5.6-terra':TEAL,'gpt-5.6-luna':SAGE,'kimi-k3':GREY}
MLAB={'claude-opus-5':'Claude Opus 5','claude-sonnet-5':'Claude Sonnet 5','gpt-5.6-sol':'GPT-5.6 Sol','gpt-5.6-terra':'GPT-5.6 Terra','gpt-5.6-luna':'GPT-5.6 Luna','kimi-k3':'Kimi K3'}
ORDER=['DDPO','DiGress','DPO','Model Soup','OPD','OpenR1','NPO','OWL','RAGEN','BTRM']
EFF=['none','low','medium','high','xhigh','max']; ESZ={'none':38,'low':60,'medium':88,'high':120,'xhigh':160,'max':210}
def cscore(c):
    if not c['checkpoints']: return None
    d=tasks[c['task']]['direction']; v=[k['score'] for k in c['checkpoints']]; return min(v) if d=='minimize' else max(v)
def better(s,r,d): return None if (s is None or r is None) else ((s<r) if d=='minimize' else (s>r))
def title(ax,t,fs=11,pad=8): ax.set_title(t,fontsize=fs,fontweight='bold',loc='left',color=INK,pad=pad)
def save(fig,n):
    fig.savefig(OUT/(n+'.pdf'),bbox_inches='tight',facecolor=WHITE)
    fig.savefig(OUT/(n+'.png'),dpi=180,bbox_inches='tight',facecolor=WHITE)
    plt.close(fig)
SYS=['claude-opus-5','gpt-5.6-sol','gpt-5.6-terra','claude-sonnet-5','gpt-5.6-luna','kimi-k3']

# ===== FIG models: FULL rank heatmap (every cell = rank 1-6) + medal & rank bars =====
R=np.array([[mr['rank'][MLAB[s]][t] for t in ORDER] for s in SYS])
Md=np.array([[mr['medal'][MLAB[s]][t] for t in ORDER] for s in SYS])
rc={1:ORANGE,2:GOLD,3:'#D8B07D',4:'#C5CCD3',5:'#DDE1E5',6:PALE}
fig,(ax,axb)=plt.subplots(1,2,figsize=(8.0,3.1),gridspec_kw={'width_ratios':[4.3,1.25]})
for i in range(len(SYS)):
    for j in range(len(ORDER)):
        r=int(R[i,j]); m=float(Md[i,j])
        # Shade by medal credit actually earned, not by rank: thresholds are set by the three best
        # distinct configuration scores, which one system may hold several of, so rank != podium.
        mc={1.0:ORANGE,0.67:GOLD,0.33:'#D8B07D'}.get(round(m,2),'#EDEFF3')
        ax.add_patch(plt.Rectangle((j-0.5,i-0.5),1,1,facecolor=mc,edgecolor='white',lw=1.5))
        tc='white' if m>=1.0 else INK
        ax.text(j,i,str(r),ha='center',va='center',fontsize=8,color=tc,fontweight='bold' if m>0 else 'normal')
ax.set_xlim(-0.5,len(ORDER)-0.5); ax.set_ylim(-0.5,len(SYS)-0.5); ax.invert_yaxis()
ax.set_xticks(range(len(ORDER))); ax.set_xticklabels(ORDER,rotation=32,ha='right',fontsize=8.5)
ax.set_yticks(range(len(SYS))); ax.set_yticklabels([MLAB[s] for s in SYS],fontsize=9.5); ax.grid(False)
for sp in ax.spines.values(): sp.set_visible(False)
med=[mr['summary'][MLAB[s]]['medal10'] for s in SYS]; rk=[mr['summary'][MLAB[s]]['rank10'] for s in SYS]
y=np.arange(len(SYS)); axb.barh(y,med,color=[MCOL[s] for s in SYS],height=0.6,zorder=3)
for i,(m,r) in enumerate(zip(med,rk)): axb.text(m+0.03,i,'%.2f'%m,va='center',fontsize=8,color=INK,fontweight='bold')
axb.set_yticks([]); axb.set_xlim(0,1.05); axb.set_xticks([0,0.5,1.0]); axb.set_xlabel('medal score  (rank in cells)',fontsize=8.5)
axb.grid(axis='y',visible=False); axb.spines['left'].set_visible(False); axb.invert_yaxis()
fig.suptitle('Rank in each cell, shaded where it earned a medal: Opus 5 ranks first on eight of ten',fontsize=11,fontweight='bold',x=0.02,ha='left',color=INK)
save(fig,'fig_models')

# ===== FIG lifecycle -> per-system OUTCOME breakdown (100% normalized) =====
def beats_recipe(c):
    t=tasks[c['task']]
    if t.get('recipe_scalar') is None:
        cell=npodom.get(c['model']+'|'+c['effort'])
        return cell['dominates'] if cell else None
    return better(cscore(c),t['recipe_scalar'],t['direction'])
def outcome(c):
    if c['accepted']<=0: return 'fail'
    return 'recipe' if beats_recipe(c) else 'below'
CATS=['recipe','below','fail']
seg=[('recipe',BLUE),('below',LIGHT),('fail','#E9D7CC')]
LEGH=[(BLUE,'beat shipped recipe'),(LIGHT,'scored, did not beat it'),('#E9D7CC','no artifact')]
fig,ax=plt.subplots(figsize=(7.7,3.2)); yy=np.arange(len(SYS))[::-1]
for i,s in enumerate(SYS):
    cs=[c for c in configs if c['model']==s]; tot=len(cs); cnt={k:sum(1 for c in cs if outcome(c)==k) for k in CATS}
    left=0.0; yb=yy[i]
    for k,col in seg:
        pct=100.0*cnt[k]/tot
        if pct>0: ax.barh(yb,pct,left=left,color=col,height=0.62,zorder=3)
        if pct>=9: ax.text(left+pct/2,yb,'%d'%round(pct)+'%',ha='center',va='center',fontsize=8,color='white' if k=='recipe' else INK,fontweight='bold' if k=='recipe' else 'normal')
        left+=pct
    ax.text(101.5,yb,'n=%d'%tot,ha='left',va='center',fontsize=7,color=GREY)
ax.set_yticks(yy); ax.set_yticklabels([MLAB[s] for s in SYS],fontsize=9.5); ax.set_xlim(0,113); ax.set_ylim(-0.6,len(SYS)-0.4); ax.grid(axis='y',visible=False)
ax.set_xlabel("share of a system's configurations, by outcome (%)")
handles=[Line2D([0],[0],marker='s',color='w',markerfacecolor=c,markersize=10,label=l) for c,l in LEGH]
ax.legend(handles=handles,fontsize=7.8,ncol=4,loc='upper center',bbox_to_anchor=(0.5,1.16),handletextpad=0.3,columnspacing=1.0)
ax.set_title('How often each system beats the recipe its repository ships',fontsize=10.2,fontweight='bold',loc='left',color=INK,pad=24)
save(fig,'fig_lifecycle')

# ===== FIG capability (unchanged, regen) =====
# r_long reduced by its BEST checkpoint under the task's direction -- the same optimistic rule
# the agents are scored under. The superseded values came from a plain mean over the replay's
# checkpoints (pooled 82.9%); these give the symmetric pooled rate of 53.0%. See TODO_FIGURES.md.
RLONG={'DDPO':0.61,'DiGress':0.44,'DPO':0.76,'OPD':0.20,'OpenR1':0.82,'BTRM':0.31}
pt=dg['per_task']
fig,ax=plt.subplots(figsize=(7.2,2.7))
from matplotlib.patches import Patch
refs=[('vs_recipe',ORANGE),('rlong',TEAL)]
NPO_RECIPE_RATE=sum(v['dominates'] for v in npodom.values())/len(npodom)
def gv(sy,key):
    if key=='rlong': return RLONG.get(sy)
    if sy=='NPO' and key=='vs_recipe': return NPO_RECIPE_RATE
    return pt[sy][key]['rate']
w=0.80; intra=0.16; gap=0.72; xx=0.0; ticks=[]; lab=[]
for sy in ORDER:
    centers=[]
    for key,c in refs:
        v=gv(sy,key)
        if v is None: continue
        ax.bar(xx,100*v,w,color=c,edgecolor='white',lw=0.6,zorder=3)
        ax.text(xx,100*v+1.4,'%d'%int(round(100*v)),ha='center',va='bottom',fontsize=6.4,fontweight='bold',color=c)
        centers.append(xx); xx+=w+intra
    ticks.append(sum(centers)/len(centers)); lab.append(sy); xx+=gap
handles=[Patch(facecolor=ORANGE,label='beat the shipped recipe'),Patch(facecolor=TEAL,label='beat the budget-matched 12 h replay')]
ax.legend(handles=handles,fontsize=8.0,ncol=3,loc='upper center',bbox_to_anchor=(0.5,1.10),frameon=False)
ax.set_xticks(ticks); ax.set_xticklabels(lab,rotation=30,ha='right',fontsize=8.5)
ax.set_ylim(0,110); ax.set_yticks([]); ax.set_xlim(-0.8,xx-gap+0.8)
for sp in ['top','right','left']: ax.spines[sp].set_visible(False)
ax.spines['bottom'].set_color(GREY)
save(fig,'fig_capability')

# ===== FIG effort: what effort buys (single panel, relative-to-none) =====
compl={'none':80,'low':80,'medium':93,'high':93,'xhigh':97,'max':97}; beat={'none':57,'low':55,'medium':68,'high':52,'xhigh':65,'max':65}
cost={'none':1.26,'low':2.61,'medium':4.15,'high':20.23,'xhigh':23.36,'max':33.11}; exp={'none':4.0,'low':4.5,'medium':9.0,'high':11.0,'xhigh':14.0,'max':16.5}; patch={'none':11.5,'low':14.5,'medium':36.5,'high':59.0,'xhigh':114.5,'max':228.0}
X="×"
fig,ax=plt.subplots(figsize=(7.6,4.4))
xs=list(range(6)); rel=lambda d:[d[e]/d['none'] for e in EFF]
for d,c,mk,lw,lab in [(cost,BLUE,'o',2.8,'cost / config'),(exp,TEAL,'^',2.2,'probe experiments'),(patch,GOLD,'D',2.2,'patch size (lines)')]:
    ax.plot(xs,rel(d),'-'+mk,color=c,lw=lw,ms=7,mec='white',mew=1.2,zorder=4,label=lab)
    ax.annotate(('%.0f'%(d['max']/d['none']))+X,(5,d['max']/d['none']),textcoords='offset points',xytext=(8,0),fontsize=9.5,color=c,fontweight='bold',va='center')
ax.plot(xs,rel(beat),'-s',color=ORANGE,lw=3.1,ms=8,mec='white',mew=1.4,zorder=6,label='win rate vs. recipe (the outcome)')
ax.annotate('~1'+X+' flat',(5,beat['max']/beat['none']),textcoords='offset points',xytext=(8,-1),fontsize=9.5,color=ORANGE,fontweight='bold',va='center')
ax.axhline(1.0,color=GREY,lw=0.9,ls=(0,(3,3)),zorder=1)
ax.set_yscale('log'); ax.set_ylim(0.8,40); ax.set_yticks([1,2,5,10,25]); ax.set_yticklabels(['1'+X,'2'+X,'5'+X,'10'+X,'25'+X],fontsize=9)
ax.set_xticks(range(6)); ax.set_xticklabels(EFF,fontsize=9.5); ax.set_xlim(-0.3,6.2)
ax.set_xlabel('reasoning effort  (Codex grid, 30 configurations per level)',fontsize=9.5)
ax.set_ylabel('median, relative to lowest effort',fontsize=9.5)
ax.set_title('Effort buys activity, not results',fontsize=12.5,fontweight='bold',color=INK,loc='left',pad=8)
ax.legend(fontsize=8.6,loc='upper left',frameon=True,framealpha=0.93)
for sp in ['top','right']: ax.spines[sp].set_visible(False)
fig.tight_layout(); save(fig,'fig_effort')

# ===== FIG cost: LINE chart, cost(x) vs score(y), per-model effort trajectory =====
def cell(model,eff):
    cs=[c for c in configs if c['model']==model and c['effort']==eff and c['accepted']>0]
    costs=[c['cost_usd'] for c in cs if c.get('cost_usd')]
    br=[beats_recipe(c) for c in cs]; br=[b for b in br if b is not None]
    return (statistics.median(costs) if costs else None, (100*sum(br)/len(br)) if br else None)
import math
fig,ax=plt.subplots(figsize=(7.3,4.3))
pts=[]
for sy in SYS:
    for e in EFF:
        co,wr=cell(sy,e)
        if co and wr is not None: pts.append((sy,e,math.log10(co),wr,co))
for sy,e,lx,wr,co in pts:
    ax.scatter(co,wr,s=ESZ.get(e,90)*0.75,color=MCOL[sy],edgecolor='white',lw=0.9,zorder=4,alpha=0.95)
xs=[p[2] for p in pts]; ys=[p[3] for p in pts]; n=len(xs)
mx=sum(xs)/n; my=sum(ys)/n
sxx=sum((x-mx)**2 for x in xs); sxy=sum((x-mx)*(y-my) for x,y in zip(xs,ys))
b=sxy/sxx; a=my-b*mx
sse=sum((y-(a+b*x))**2 for x,y in zip(xs,ys)); syx=(sse/(n-2))**0.5; tval=2.056
gx=[math.log10(0.5)+ (math.log10(70)-math.log10(0.5))*i/60.0 for i in range(61)]
gy=[a+b*x for x in gx]; band=[tval*syx*(1.0/n+(x-mx)**2/sxx)**0.5 for x in gx]
xr=[10**x for x in gx]
ax.fill_between(xr,[g-bd for g,bd in zip(gy,band)],[g+bd for g,bd in zip(gy,band)],color=INK,alpha=0.10,zorder=2)
ax.plot(xr,gy,'-',color=INK,lw=2.4,zorder=5)
syy_=sum((y-my)**2 for y in ys); rval=sxy/(sxx*syy_)**0.5
POOL=100.0*sum(1 for c in configs if c['accepted']>0 and beats_recipe(c))/sum(1 for c in configs if c['accepted']>0 and beats_recipe(c) is not None)
ax.axhline(POOL,color=GREY,lw=0.9,ls=(0,(3,3)),zorder=1)
ax.text(0.58,POOL+1.0,'suite mean',fontsize=7.5,color=GREY,ha='left')
ax.text(0.035,0.955,'Pearson r = %.2f  (weak; ~%.0f%% of variance)\nfit: %+.1f win-rate pts per 10× cost'%(rval,100*rval*rval,b),transform=ax.transAxes,va='top',ha='left',fontsize=8.6,color=INK,bbox=dict(boxstyle='round,pad=0.45',fc=PALE_ORANGE,ec='#E4DCCF',lw=0.8))
ax.text(0.035,0.055,r'cheapest third: 55% @ \$3/cfg      priciest third: 60% @ \$35/cfg',transform=ax.transAxes,va='bottom',ha='left',fontsize=8.0,color=INK,style='italic')
from matplotlib.lines import Line2D
h=[Line2D([0],[0],marker='o',color='none',markerfacecolor=MCOL[sy],markeredgecolor='white',markersize=8,label=MLAB[sy]) for sy in SYS]
ax.legend(handles=h,fontsize=7.4,loc='lower right',frameon=True,framealpha=0.92,ncol=2,handletextpad=0.3,columnspacing=0.9)
ax.set_xscale('log'); ax.set_xlim(0.5,72); ax.set_ylim(40,84)
ax.set_xticks([1,2,5,10,20,50]); ax.set_xticklabels(['1','2','5','10','20','50'],fontsize=8.5); ax.tick_params(labelsize=8.5)
ax.set_xlabel('median exploration cost per configuration  (USD, log)',fontsize=9.5)
ax.set_ylabel('win rate over shipped recipe (%)',fontsize=9.5)
ax.set_title('Cost barely moves the score',fontsize=11.5,fontweight='bold',color=INK,loc='left',pad=10)
for sp in ['top','right']: ax.spines[sp].set_visible(False)
fig.tight_layout()
save(fig,'fig_cost')
# ===== FIG teaser (Figure 1): results-forward, 2-row (capability | standings | measurement) =====
X=chr(0x00D7); ARR=chr(0x2192); DSH=chr(0x2014); MID=chr(0x00B7)
from matplotlib.patches import Rectangle
figT=plt.figure(figsize=(9.4,5.0))
axR=figT.add_axes([0.03,0.875,0.94,0.10]); axR.set_xlim(0,10); axR.set_ylim(0,1); axR.axis('off')
stages=['10 frozen repos','agent '+MID+' 4 h, 1 GPU','source-only patch','fresh 12 h retrain','independent eval']
cx=[1.2,3.3,5.15,7.0,8.72]
for x,st in zip(cx,stages):
    axR.text(x,0.5,st,ha='center',va='center',fontsize=7.0,color=INK,bbox=dict(boxstyle='round,pad=0.4',fc='#F4F6F9',ec=GREY,lw=1.0))
for i in range(len(cx)-1):
    axR.annotate('',xy=(cx[i+1]-0.82,0.5),xytext=(cx[i]+0.82,0.5),arrowprops=dict(arrowstyle='-|>',color=GREY,lw=1.1))
axR.annotate('',xy=(9.72,0.5),xytext=(cx[-1]+0.74,0.5),arrowprops=dict(arrowstyle='-|>',color=GREY,lw=1.1))
axR.text(9.78,0.5,'score',ha='left',va='center',fontsize=7.4,color=INK,fontweight='bold')
figT.text(0.05,0.80,'WHAT THE AGENTS ACHIEVE',fontsize=9,color=INK,fontweight='bold')
figT.text(0.05,0.778,'share of scored configs beating each reference',fontsize=6.8,color=GREY)
figT.text(0.55,0.80,'WHICH SYSTEM WINS',fontsize=9,color=INK,fontweight='bold')
figT.text(0.55,0.778,'medal score (podium credit over 10 tasks) '+MID+' Claude Opus 5 leads',fontsize=6.8,color=GREY)
axB=figT.add_axes([0.05,0.47,0.40,0.27])
vals=[('beats the frozen start',81.8,SAGE),('beats the shipped recipe',62.6,GOLD),('beats a strong recipe',18.6,CORAL)]
for (lab,v,c),y in zip(vals,[2,1,0]):
    axB.barh(y,v,height=0.5,color=c,edgecolor='white',lw=1.0,zorder=3)
    axB.text(v+2,y,('%.1f'%v)+'%',va='center',ha='left',fontsize=11,fontweight='bold',color=c)
    axB.text(0,y+0.42,lab,va='bottom',ha='left',fontsize=8.2,color=INK)
axB.axvline(100,color=GREY,lw=0.7,ls=(0,(3,3)),zorder=1)
axB.set_xlim(0,126); axB.set_ylim(-0.6,2.95); axB.axis('off')
axS=figT.add_axes([0.55,0.44,0.42,0.31]); axS.set_xlim(0,1); axS.set_ylim(0,1); axS.axis('off')
MEDAL=[('Claude Opus 5',0.833,CORAL),('GPT-5.6 Sol',0.500,NAVY),('GPT-5.6 Terra',0.268,TEAL),('Claude Sonnet 5',0.167,GOLD),('GPT-5.6 Luna',0.133,SAGE),('Kimi K3',0.0,GREY)]
rowy=[0.90,0.73,0.56,0.39,0.22,0.05]
for (nm,sc,c),y in zip(MEDAL,rowy):
    bd='bold' if nm=='Claude Opus 5' else 'normal'
    axS.text(0.0,y,nm,fontsize=7.6,color=INK,va='center',ha='left',fontweight=bd)
    bw=sc/0.85*0.34
    axS.add_patch(Rectangle((0.52,y-0.052),bw,0.104,color=c,ec='white',lw=0.5))
    axS.text(0.52+bw+0.015,y,'%.2f'%sc,fontsize=7.4,color=c,va='center',ha='left',fontweight=bd)
figT.text(0.05,0.355,'HOW THE AGENTS WORK',fontsize=9,color=INK,fontweight='bold')
figT.text(0.05,0.333,'behaviour behind the numbers, read from the exploration logs',fontsize=6.8,color=GREY)
axC=figT.add_axes([0.05,0.12,0.92,0.19]); axC.set_xlim(0,1); axC.set_ylim(0,1); axC.axis('off')
beh=[('8'+X+' spread in spend','across systems, yet the leader (Opus) is only mid-cost',NAVY,0.0),
     ('158 of 280 patches','change only how the run is managed, not the learning rule',TEAL,0.54)]
for big,desc,c,xx in beh:
    axC.text(xx,0.78,big,fontsize=12.5,fontweight='bold',color=c,ha='left',va='center')
    axC.text(xx,0.30,desc,fontsize=7.1,color=INK,ha='left',va='center')
figT.text(0.05,0.03,'Coding agents reliably recover a competent default '+DSH+' they rarely surpass a strong one.',fontsize=11.5,fontweight='bold',color=INK,ha='left')
figT.text(0.97,0.84,'6 systems '+MID+' 290 configs '+MID+' 792 scored artifacts',fontsize=7.2,color=GREY,ha='right',va='center')
# The paper teaser is generated by make_task_cards.py + make_teaser.py.  Keep
# this old dashboard prototype out of the production output directory.
plt.close(figT)
# ===== FIG lifecycle GRID -> per (model x effort) outcome breakdown (100% normalized) =====
gr=[]
for s in SYS:
    for e in EFF:
        cs=[c for c in configs if c['model']==s and c['effort']==e]
        if not cs: continue
        cnt={k:sum(1 for c in cs if outcome(c)==k) for k in CATS}; gr.append((s,e,cnt,len(cs)))
figG,axG=plt.subplots(figsize=(7.4,7.6))
yv=[]; y=0.0; last=None; groups={}
for (s,e,cnt,tot) in gr:
    if last is not None and s!=last: y-=0.9
    yv.append(y); groups.setdefault(s,[]).append(y); y-=1.0; last=s
EAB={'none':'none','low':'low','medium':'med','high':'high','xhigh':'xhigh','max':'max'}
for (s,e,cnt,tot),yb in zip(gr,yv):
    left=0.0
    for k,col in seg:
        pct=100.0*cnt[k]/tot
        if pct>0: axG.barh(yb,pct,left=left,color=col,height=0.74,zorder=3)
        left+=pct
    axG.text(-1.2,yb,EAB[e],ha='right',va='center',fontsize=7.0,color=INK)
for s,ys in groups.items():
    axG.text(-14.5,(min(ys)+max(ys))/2.0,MLAB[s],ha='center',va='center',fontsize=8.6,fontweight='bold',color=MCOL[s],rotation=90,clip_on=False)
axG.set_yticks([]); axG.set_xlim(0,100); axG.set_ylim(min(yv)-0.8,max(yv)+0.8)
for sp in ['top','right','left']: axG.spines[sp].set_visible(False)
axG.set_xlabel("share of the cell's ten tasks, by outcome (%)")
hG=[Line2D([0],[0],marker='s',color='w',markerfacecolor=c,markersize=10,label=l) for c,l in LEGH]
axG.legend(handles=hG,fontsize=7.8,ncol=4,loc='upper center',bbox_to_anchor=(0.5,1.045),handletextpad=0.3,columnspacing=1.0)
axG.set_title('Outcome mix by model and effort',fontsize=11.5,fontweight='bold',loc='left',color=INK,pad=16)
figG.subplots_adjust(left=0.15,right=0.97,top=0.92,bottom=0.07)
save(figG,'fig_lifecycle_grid')
print("done")
