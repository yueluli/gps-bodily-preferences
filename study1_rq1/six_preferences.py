from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]; O=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'Bodily_standalone'))
from bodily_comparison import _read_model_block
A=R/'GPS1000_joint/archive/GPS1000_four_groups'
spec=json.loads((A/'results/experiment.json').read_text()); cohort=pd.read_csv(A/'cohort.csv',dtype={'id_gallup':str}); assign=pd.read_csv(A/'assignments.csv',dtype={'id_gallup':str}).set_index('id_gallup').loc[cohort.id_gallup]
arms=['baseline_repeat','sleep_levels','steps_levels']; raw={}
for arm in arms:
 result,status=_read_model_block(A/'results/conditions'/arm/'replicate_001',{'id':'gpt-6-luna','key':'gpt6_luna'},cohort,spec)
 assert status['complete_interviews']==1000
 raw[arm]=result[0].set_index('id_gallup').loc[assign.index]
weights={'风险偏好':{'staircase_risk':.4729985,'will_to_take_risk':.5270015},'耐心':{'staircase_patience':.7115185,'will_to_giveup_today':.2884815},'利他':{'will_to_good_cause':.6350048,'hypo_donation_proportion':.3649952},'正向互惠':{'will_to_return_favor':.4847038,'size_gift':.5152962},'负向互惠':{'punish_oneself':.6261938/2,'punish_others':.6261938/2,'will_to_ravenge':.3738062},'信任':{'trust':1}}
pool=pd.concat(raw.values()); mu=pool.mean(); sd=pool.std(ddof=1)
components=set(k for w in weights.values() for k in w); assert (sd[list(components)]>0).all()
z={k:(v-mu)/sd for k,v in raw.items()}
scores={k:pd.DataFrame({p:sum(v[c]*w for c,w in ws.items()) for p,ws in weights.items()}) for k,v in z.items()}
ps=pd.concat(scores.values()); pm=ps.mean(); pstd=ps.std(ddof=1)
scores={k:(v-pm)/pstd for k,v in scores.items()}
rows=[]; rng=np.random.default_rng(42)
for arm,col in zip(arms[1:],['sleep_level','steps_level']):
 d=scores[arm]-scores[arms[0]]
 for level in sorted(assign[col].unique()):
  g=d.loc[assign[col]==level]; assert len(g)==200
  ix=rng.integers(0,200,(3000,200))
  for p in weights:
   x=g[p].to_numpy(); lo,hi=np.quantile(x[ix].mean(1),[.025,.975]); rows.append(dict(condition=arm,level=level,preference=p,n=200,mean_shift=x.mean(),ci_low=lo,ci_high=hi))
f=pd.DataFrame(rows); f.to_csv(O/'six_preferences_changes.csv',index=False)
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial Unicode MS','DejaVu Sans'],'font.size':12,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(2,3,figsize=(15,9),sharey=True)
for ax,p in zip(axs.flat,weights):
 for j,arm in enumerate(arms[1:]):
  g=f[(f.condition==arm)&(f.preference==p)].sort_values('level'); xx=np.arange(5)+(j-.5)*.08
  ax.errorbar(xx,g.mean_shift,yerr=[g.mean_shift-g.ci_low,g.ci_high-g.mean_shift],fmt='o-',capsize=3,lw=2,color=['#2864b4','#d07a28'][j],label=['睡眠线索','步数线索'][j])
 ax.axhline(0,color='#777',lw=1); ax.set_xticks(range(5),['最低','较低','中间','较高','最高']); ax.set_title(p,fontsize=17,pad=13); ax.grid(axis='y',alpha=.15)
for ax in axs[:,0]: ax.set_ylabel('相对本人 baseline 的变化（共同标尺 SD）')
axs[0,0].legend(frameon=False)
fig.suptitle('Study 1｜六种综合偏好相对 baseline 的变化',fontsize=23,y=.98)
fig.text(.5,.925,'同一批 1,000 个模拟个体 · 每个线索五档 · 每档 200 人',ha='center',color='#555')
fig.text(.5,.075,'睡眠五档：5 / 6 / 7 / 8 / 9 小时　　步数五档：1,879 / 3,279 / 4,727 / 6,715 / 10,955 步',ha='center')
fig.text(.5,.043,'原有 GPS 题目权重；三组合并建立固定共同标尺。误差线：95% 配对 bootstrap 区间（未作多重比较校正）。',ha='center',fontsize=10)
fig.text(.5,.017,'正值＝该偏好得分提高，负值＝降低；档位间为不同个体。区间以本次生成及固定标尺为条件，观测差异包含生成波动。',ha='center',fontsize=10)
fig.tight_layout(rect=[0,.11,1,.9]); fig.savefig(O/'six_preferences_changes.png',dpi=180); fig.savefig(O/'six_preferences_changes.pdf')
(O/'six_preferences_method.md').write_text('六种偏好沿用 run_fig2_baseline.py 的组合权重与 score_raw 自适应阶梯计分。对 baseline、sleep_levels、steps_levels 共3000条完整记录合并计算各题均值及样本标准差，统一标准化；加权组合后再用三组合并的组合分均值及标准差统一缩放。所有条件共用固定标尺，未分别居中。每档按ID与baseline配对，3000次bootstrap，种子42；区间不重估标尺、不校正多重比较，也不覆盖新一轮模型生成波动。此为RQ1共同标尺分析，与旧版逐条件标准化MSE分析不同。全部3000套访谈经已有协议重放校验。\n')
print('Saved six-panel PNG, PDF, CSV and method note.')
