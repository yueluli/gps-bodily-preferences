from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]; OUT=Path(__file__).resolve().parent
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial Unicode MS','DejaVu Sans'],'axes.spines.top':False,'axes.spines.right':False,'font.size':11})
arc=ROOT/'GPS1000_joint/archive/GPS1000_four_groups'
a=pd.read_csv(arc/'assignments.csv',dtype={'id_gallup':str}).set_index('id_gallup')
items=['will_to_take_risk','will_to_giveup_today','will_to_good_cause','will_to_return_favor','will_to_ravenge','trust','punish_oneself','punish_others']
labels=['冒险意愿','等待意愿','公益意愿','回报他人意愿','报复意愿','信任','付出代价惩罚伤害自己者','付出代价惩罚伤害他人者']
colors=['#2864b4','#d07a28']; arms=['sleep_levels','steps_levels']
def read(arm):
 p=arc/'results/conditions'/arm/'replicate_001/responses.sqlite3'
 with sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True) as con:
  f=pd.read_sql_query("select person,item,value from answers where status='success'",con)
 f['person']=f.person.astype(str)
 return f.pivot(index='person',columns='item',values='value').loc[a.index,items].astype(float)
b=read('baseline_repeat'); rng=np.random.default_rng(42); rows=[]
for arm,col in zip(arms,['sleep_level','steps_level']):
 d=read(arm)-b
 assert len(d)==1000 and d.notna().all().all()
 for level in sorted(a[col].unique()):
  g=d.loc[a[col].eq(level)]; assert len(g)==200
  ix=rng.integers(0,len(g),size=(2000,len(g)))
  for item in items:
   x=g[item].to_numpy(); lo,hi=np.quantile(x[ix].mean(axis=1),[.025,.975])
   rows.append(dict(condition=arm,level=level,item=item,n=len(x),mean_shift=x.mean(),ci_low=lo,ci_high=hi,mean_absolute_shift=np.abs(x).mean(),fraction_changed=(x!=0).mean()))
 s=pd.read_csv(ROOT/'GPS1000_joint/comparison/paired_raw_shifts.csv').query('condition == @arm').set_index('item')
 assert np.allclose(d.mean(),s.loc[items,'mean_shift'])
f=pd.DataFrame(rows); f.to_csv(OUT/'level_changes.csv',index=False)
s=pd.read_csv(ROOT/'GPS1000_joint/comparison/paired_raw_shifts.csv'); s=s[s.condition.isin(arms)&s.item.isin(items)]
fig,axs=plt.subplots(1,2,figsize=(13,6.5),gridspec_kw={'width_ratios':[1.3,1]})
y=np.arange(len(items))
for j,arm in enumerate(arms):
 g=s[s.condition.eq(arm)].set_index('item').loc[items]; yy=y+(j-.5)*.23
 axs[0].errorbar(g.mean_shift,yy,xerr=[g.mean_shift-g.ci_low,g.ci_high-g.mean_shift],fmt='o',capsize=3,color=colors[j],label=['睡眠五档','步数五档'][j])
 axs[1].barh(yy,g.fraction_changed*100,height=.21,color=colors[j])
axs[0].set_yticks(y,labels); axs[0].invert_yaxis(); axs[0].axvline(0,color='#888',lw=1); axs[0].set_xlabel('平均配对变化（线索 − baseline，原始量表分）'); axs[0].legend()
axs[1].set_yticks(y,labels=['']*len(y)); axs[1].invert_yaxis(); axs[1].set_xlabel('回答发生变化的模拟个体（%）'); axs[1].set_xlim(0,60)
axs[0].set_title('方向与净变化量'); axs[1].set_title('多少人的回答改变了')
fig.suptitle('Study 1｜睡眠与步数线索相对 baseline 的观测变化',fontsize=18)
fig.text(.5,.015,'每条件 N = 1,000；横线为逐项 95% 配对 bootstrap 区间，未作多重比较校正。变化包含生成波动。',ha='center',fontsize=10)
fig.tight_layout(rect=[0,.05,1,.94]); fig.savefig(OUT/'overall_changes.png',dpi=180); plt.close(fig)
fig,axs=plt.subplots(2,4,figsize=(16,8.2))
for ax,item,label in zip(axs.flat,items,labels):
 for j,arm in enumerate(arms):
  g=f[(f.condition==arm)&(f.item==item)].sort_values('level'); xx=np.arange(5)+(j-.5)*.08
  ax.errorbar(xx,g.mean_shift,yerr=[g.mean_shift-g.ci_low,g.ci_high-g.mean_shift],fmt='o-',capsize=2,color=colors[j],label=['睡眠','步数'][j])
 ax.axhline(0,color='#888',lw=1); ax.set_xticks(range(5),['最低','较低','中间','较高','最高']); ax.set_title(label); ax.set_ylabel('线索 − 本人 baseline'); ax.grid(axis='y',alpha=.15)
axs.flat[0].legend(); fig.suptitle('每档 200 人｜分档后的原始回答变化',fontsize=19)
fig.text(.5,.045,'睡眠：5 / 6 / 7 / 8 / 9 小时　　步数：1,879 / 3,279 / 4,727 / 6,715 / 10,955 步',ha='center')
fig.text(.5,.015,'各点匹配该档相同 ID 的 baseline；档位间是不同个体。95% 区间未校正；连线辅助阅读，不代表线性效应。',ha='center',fontsize=10)
fig.tight_layout(rect=[0,.08,1,.93]); fig.savefig(OUT/'level_changes.png',dpi=180)
print(f[f.item.isin(['trust','will_to_take_risk','will_to_return_favor'])].to_string(index=False))
