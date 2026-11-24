"""Analyze complete heart-rate pilot; refuses partial result claims."""
import sys,sqlite3,json,re
from pathlib import Path
import numpy as np,pandas as pd
R=Path(__file__).resolve().parents[3]; O=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'Bodily_standalone'))
import run_fig2_baseline as base
from bodily_comparison import _read_model_block,_metrics,_interval
A=R/'GPS1000_joint/archive/GPS1000_four_groups';M={'id':'gpt-6-luna','key':'gpt6_luna'}
c=pd.read_csv(O/'data/sampled_participants.csv',dtype={'id_gallup':str});spec=json.loads((A/'results/experiment.json').read_text())
allc=pd.read_csv(A/'cohort.csv',dtype={'id_gallup':str});block,status=_read_model_block(A/'results/conditions/baseline_repeat/replicate_001',M,allc,spec)
assert block is not None
baseline_raw=block[0].set_index('id_gallup').loc[c.id_gallup].reset_index(); baseline_raw.to_csv(O/'data/baseline_original.csv',index=False)
gps=base.read_gps(base.DEFAULT_GPS).set_index('id_gallup').loc[c.id_gallup].reset_index();gps[['id_gallup',*base.PREFERENCES]].to_csv(O/'data/human_reference.csv',index=False)
db=sqlite3.connect('file:'+str(O/'data/responses.sqlite3')+'?mode=ro',uri=True)
rows=pd.read_sql_query('select person,arm,item,stage,status,choice,reason,raw,timestamp,attempts,request_order,error from records',db);db.close();rows.person=rows.person.astype(str)
counts=rows.groupby(['arm','stage','status']).size().rename('n').reset_index();counts.to_csv(O/'analysis/response_validation.csv',index=False)
if len(rows.query('status=="valid"'))!=12000:raise SystemExit('Incomplete, valid stage records '+str(len(rows.query('status=="valid"')))+' / 12000')
frames={'baseline_original':baseline_raw};long=[];reason_rows=[]
for arm in ['baseline_with_reason','bodily_context','numerical_placebo']:
 one=rows.query('arm==@arm and stage==1').set_index(['person','item']);two=rows.query('arm==@arm and stage==2').set_index(['person','item'])
 assert len(one)==len(two)==2000 and one.status.eq('valid').all() and two.status.eq('valid').all()
 raw=[]
 for pid in c.id_gallup:
  answers={}
  while (q:=base.next_question(answers,spec['calibration'])) is not None:
   r=one.loc[(pid,q.key)];answer=base.parse_answer(q,str(r.choice));answers[q.key]=answer
   v=two.loc[(pid,q.key)];t=json.loads(v.reason)
   long.append(dict(participant_id=pid,condition=arm,question_id=q.key,choice=answer,reason=r.reason,context_influence=t['context_influence'],influence_reason=t['influence_reason'],original_question=q.text,additional_context=json.loads((O/'config/experiment_config.json').read_text())['conditions'][arm],stage1_raw_response=r.raw,stage2_raw_response=v.raw,stage1_valid=True,stage2_valid=True,timestamp=r.timestamp,stage2_timestamp=v.timestamp,stage1_attempts=r.attempts,stage2_attempts=v.attempts))
  raw.append({'id_gallup':pid,**base.score_raw(answers,spec['calibration'])})
 frames[arm]=pd.DataFrame(raw);frames[arm].to_csv(O/f'data/{arm}.csv',index=False)
pd.DataFrame(long).to_csv(O/'data/combined_results.csv',index=False)
# Keep original six preference metrics and report paired person-level uncertainty.
metrics=[];errors={}
for arm,raw in frames.items():
 score=base.score_responses(raw,M['key']);m,e=_metrics(score,gps,M)
 metrics.extend([dict(condition=arm,**r) for r in m]);errors[arm]=e
pd.DataFrame(metrics).to_csv(O/'analysis/prediction_accuracy.csv',index=False)
comparisons=[('bodily_context','baseline_with_reason'),('numerical_placebo','baseline_with_reason'),('bodily_context','numerical_placebo'),('baseline_with_reason','baseline_original')]
paired=[];improve=[]
for a,b in comparisons:
 aa=frames[a].set_index('id_gallup').loc[c.id_gallup];bb=frames[b].set_index('id_gallup').loc[c.id_gallup]
 for item in aa.columns:
  d=(aa[item]-bb[item]).to_numpy();lo,hi=_interval(d,(100,3000,42));paired.append(dict(left=a,right=b,item=item,n=100,mean_change=d.mean(),absolute_change=np.abs(d).mean(),fraction_changed=np.mean(d!=0),ci_low=lo,ci_high=hi))
 for pref in base.PREFERENCES:
  key=('individual',pref)
  if key in errors[a] and key in errors[b]:
   d=errors[b][key]-errors[a][key];lo,hi=_interval(d,(100,3000,42));improve.append(dict(left=a,right=b,preference=pref,improvement=d.mean(),ci_low=lo,ci_high=hi))
pd.DataFrame(paired).to_csv(O/'analysis/paired_comparisons.csv',index=False);pd.DataFrame(improve).to_csv(O/'analysis/predictive_improvement.csv',index=False)
# Exact-text mention counts, distinct from semantic coding.
ld=pd.DataFrame(long);patterns={'heart_rate':r'heart rate|heartbeat|bpm','bodily_state':r'body|physical|resting|seated','numeric_72':r'(?<!\d)72(?!\d)','calmness':r'calm|relax','stress':r'stress','health':r'health'}
for key,pattern in patterns.items():
 ld['reason_'+key]=ld.reason.str.contains(pattern,case=False,regex=True,na=False)
 ld['self_'+key]=ld.influence_reason.fillna('').str.contains(pattern,case=False,regex=True)
ld.to_csv(O/'analysis/reason_analysis.csv',index=False)
ld.groupby(['condition','context_influence']).size().rename('n').reset_index().to_csv(O/'analysis/context_influence_analysis.csv',index=False)
(O/'analysis/reason_codebook.json').write_text(json.dumps({'method':'exact lexical pattern only; not semantic coding','patterns':patterns},indent=2))
summary=ld.groupby('condition').agg(spontaneous_heart_rate=('reason_heart_rate','mean'),spontaneous_bodily=('reason_bodily_state','mean'),self_heart_rate=('self_heart_rate','mean'),reported_yes=('context_influence',lambda x:(x=='yes').mean())).to_string()
(O/'report/experiment_report.md').write_text('# Heart Rate Pilot 实验报告\n\n已完成100人、三组、每人20题、两阶段共12,000条有效输出。Original Baseline从历史归档复用。\n\n## 两阶段报告\n\n'+summary+'\n\n预测误差见 `analysis/prediction_accuracy.csv`；配对比较见 `analysis/paired_comparisons.csv`，改善见 `analysis/predictive_improvement.csv`。所有区间以本次生成和固定样本为条件。Reason及自我报告不能证明内部机制。固定72 bpm是模拟提示而非实际测量，100人仅为pilot。\n')
print('Analysis complete')
