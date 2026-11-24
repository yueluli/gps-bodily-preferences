from pathlib import Path
import sys
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parents[1];F=O/'figures';F.mkdir(exist_ok=True)
weights={'风险承担':{'staircase_risk':.4729985,'will_to_take_risk':.5270015},'耐心':{'staircase_patience':.7115185,'will_to_giveup_today':.2884815},'负互惠':{'punish_oneself':.6261938/2,'punish_others':.6261938/2,'will_to_ravenge':.3738062},'正互惠':{'will_to_return_favor':.4847038,'size_gift':.5152962},'利他':{'will_to_good_cause':.6350048,'hypo_donation_proportion':.3649952},'信任':{'trust':1}}
arms=['baseline_with_reason','bodily_context','numerical_placebo'];raw={a:pd.read_csv(O/f'data/{a}.csv',dtype={'id_gallup':str}).set_index('id_gallup') for a in arms};ids=raw[arms[0]].index
assert all(raw[a].index.equals(ids) for a in arms)
b=raw[arms[0]];mu=b.mean();sd=b.std(ddof=1);assert all(sd[c]>0 for w in weights.values() for c in w)
z={a:(raw[a]-mu)/sd for a in arms};scores={a:pd.DataFrame({p:sum(v[c]*w for c,w in ws.items()) for p,ws in weights.items()},index=ids) for a,v in z.items()};bs=scores[arms[0]].std(ddof=1);rng=np.random.default_rng(42);ix=rng.integers(0,100,(3000,100));rows=[]
for arm in arms[1:]:
 for p in weights:
  d=((scores[arm][p]-scores[arms[0]][p])/bs[p]).to_numpy();lo,hi=np.quantile(d[ix].mean(axis=1),[.025,.975]);rows.append(dict(condition=arm,preference=p,n=100,mean=d.mean(),ci_low=lo,ci_high=hi))
f=pd.DataFrame(rows);f.to_csv(O/'analysis/preference_score_shifts.csv',index=False)
plt.rcParams.update({'font.sans-serif':['Arial Unicode MS','DejaVu Sans'],'font.size':13,'text.color':'#233954','axes.labelcolor':'#233954','xtick.color':'#233954','pdf.fonttype':42})
fig=plt.figure(figsize=(12,8),facecolor='white');ax=fig.add_axes([.19,.17,.54,.62]);colors=['#008588','#bd5317'];names=['静息心率 72 次/分','非身体数字 72']
lim=max(.2,np.ceil(max(abs(f.ci_low).max(),abs(f.ci_high).max())*10)/10)
for j,(arm,color) in enumerate(zip(arms[1:],colors)):
 for i,p in enumerate(weights):
  r=f[(f.condition==arm)&(f.preference==p)].iloc[0];y=5-i+(.14 if j==0 else -.14);ax.plot([r.ci_low,r.ci_high],[y,y],color=color,lw=2.2);ax.plot(r['mean'],y,'D',color=color,ms=7);ax.text(1.06,y,f"{r['mean']:+.3f}  [{r.ci_low:+.3f}, {r.ci_high:+.3f}]",transform=ax.get_yaxis_transform(),color=color,fontsize=11,va='center')
ax.set_ylim(-.65,5.65);ax.set_xlim(-lim,lim);ax.set_xticks([-lim,0,lim]);ax.set_yticks(range(6),list(weights)[::-1]);ax.tick_params(axis='both',length=0,pad=12);ax.tick_params(axis='y',labelsize=18,pad=40)
for s in ax.spines.values():s.set_visible(False)
ax.grid(axis='x',color='#c6d0dc',lw=.8);ax.set_axisbelow(True);ax.set_xlabel('相对于带理由 baseline 的变化（该组标准差）',labelpad=18,fontsize=16)
fig.text(.035,.93,'加入心率或数字信息后，六项偏好平均改变了多少？',fontsize=24);fig.text(.035,.876,'同一人的条件得分减去带理由 baseline · 100 人配对 · 点为平均差，线为 95% bootstrap 区间',fontsize=14)
for x,c,n in zip([.2,.47],colors,names):fig.text(x,.825,'● '+n,color=c,fontsize=15)
fig.text(.035,.034,'原 GPS 组合权重；各组共用带理由 baseline 标尺。3,000 次配对重采样；区间未校正多重比较。',fontsize=10)
fig.text(.035,.012,'每人每条件仅一次生成，区间不包含重新调用模型带来的波动；历史 baseline 仅为参考。',fontsize=10)
fig.savefig(F/'figure_9_preference_shifts_zh.png',dpi=180);fig.savefig(F/'figure_9_preference_shifts_zh.pdf')
print(f.to_string(index=False))
