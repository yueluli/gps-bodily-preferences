"""Create eight publication-sized PNG and PDF plots from completed aggregate analysis."""
from pathlib import Path
import pandas as pd,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parents[1];F=O/'figures';F.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial Unicode MS','DejaVu Sans'],'axes.spines.top':False,'axes.spines.right':False})
def save(fig,name):
 fig.tight_layout();fig.savefig(F/(name+'.png'),dpi=180);fig.savefig(F/(name+'.pdf'));plt.close(fig)
c=pd.read_csv(O/'data/sampled_participants.csv');full=pd.read_csv(O.parents[1]/'GPS1000_joint/archive/GPS1000_four_groups/cohort.csv')
fig,ax=plt.subplots(1,2,figsize=(12,4));ax[0].hist(full.age,bins=15,alpha=.5,label='1000');ax[0].hist(c.age,bins=15,alpha=.5,label='100');ax[0].legend();ax[0].set_title('Age');pd.DataFrame({'all':full.gender.value_counts(normalize=True),'sample':c.gender.value_counts(normalize=True)}).plot.bar(ax=ax[1]);ax[1].set_title('Gender');save(fig,'figure_1_sampling')
m=pd.read_csv(O/'analysis/prediction_accuracy.csv');ind=m.query('level=="individual" and status=="ok"')
fig,ax=plt.subplots(figsize=(12,5));ind.pivot(index='preference',columns='condition',values='mse').plot.bar(ax=ax);ax.set_ylabel('MSE to human GPS');save(fig,'figure_3_prediction_error')
fig,ax=plt.subplots(figsize=(12,5));ind.pivot(index='preference',columns='condition',values='pearson_r').plot.bar(ax=ax);ax.set_ylabel('Pearson r to human GPS');save(fig,'figure_2_preference_comparison')
i=pd.read_csv(O/'analysis/predictive_improvement.csv');i=i.query('right=="baseline_with_reason" or (left=="bodily_context" and right=="numerical_placebo")');fig,ax=plt.subplots(figsize=(12,5));i.assign(comparison=i['left']+' vs '+i['right']).pivot(index='preference',columns='comparison',values='improvement').plot.bar(ax=ax);ax.axhline(0,color='black',lw=.8);ax.set_ylabel('Improvement (error decrease)');save(fig,'figure_4_predictive_improvement')
p=pd.read_csv(O/'analysis/paired_comparisons.csv');fig,ax=plt.subplots(figsize=(12,5));p.query('right=="baseline_with_reason"').pivot(index='item',columns='left',values='fraction_changed').plot.bar(ax=ax);ax.set_ylabel('Fraction changed');save(fig,'figure_5_decision_change')
r=pd.read_csv(O/'analysis/reason_analysis.csv');cols=[x for x in r if x.startswith('reason_')];fig,ax=plt.subplots(figsize=(10,5));r.groupby('condition')[cols].mean().T.plot.bar(ax=ax);ax.set_ylabel('Share of reasons (lexical)');save(fig,'figure_6_reason_analysis')
x=pd.read_csv(O/'analysis/context_influence_analysis.csv');fig,ax=plt.subplots(figsize=(8,5));x.pivot(index='condition',columns='context_influence',values='n').fillna(0).pipe(lambda a:a.div(a.sum(axis=1),axis=0)).plot.bar(stacked=True,ax=ax);ax.set_ylabel('Share');save(fig,'figure_7_context_influence')
ld=pd.read_csv(O/'data/combined_results.csv');b=ld.query('condition=="baseline_with_reason"').set_index(['participant_id','question_id']);ld=ld.query('condition!="baseline_with_reason"').copy();ld['changed']=ld.apply(lambda row: row.choice!=b.loc[(row.participant_id,row.question_id),'choice'],axis=1);fig,ax=plt.subplots(figsize=(8,5));pd.crosstab(ld.changed,ld.context_influence,normalize='index').plot.bar(stacked=True,ax=ax);ax.set_ylabel('Share');save(fig,'figure_8_behavior_self_report')
print('Eight figures saved')
