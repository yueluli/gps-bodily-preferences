"""Frozen 100-person heart-rate context pilot; local data and keys stay local."""
import argparse,csv,hashlib,json,re,sqlite3,sys,time,threading,concurrent.futures,os
from datetime import datetime,timezone
from pathlib import Path
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'Bodily_standalone'))
import run_fig2_baseline as base
from bodily_comparison import _read_model_block
from run_distribution_comparison import curl_open
ARCH=ROOT/'GPS1000_joint/archive/GPS1000_four_groups'; MODEL={'id':'gpt-6-luna','key':'gpt6_luna'}
ARMS={'baseline_with_reason':'','bodily_context':'You are seated and resting. Your current heart rate is 72 beats per minute.','numerical_placebo':'You are seated and resting. A nearby sheet records 72 as its final reference number.'}
STAGE1='''Make your decision based on the information provided.\n\nFirst, provide your choice. Then, briefly explain the main reason for your choice in one complete sentence of no more than 20 words.\n\nReturn only valid JSON using the following format:\n\n{\n  "choice": "<your choice>",\n  "reason": "<one brief sentence>"\n}'''
STAGE2='''Did any contextual information beyond the economic decision itself influence your choice?\n\nIf yes, briefly identify the information and explain its influence in one sentence of no more than 20 words.\n\nIf you are uncertain, briefly explain why.\n\nDo not revise your previous choice.\n\nReturn only valid JSON using the following format:\n\n{\n  "context_influence": "yes, no, or uncertain",\n  "influence_reason": "<one brief sentence or null>"\n}'''
SEED=42

def sample():
 allp=pd.read_csv(ARCH/'cohort.csv',dtype={'id_gallup':str}); assert len(allp)==1000 and allp.id_gallup.is_unique
 # Stratified allocation by country and age quartile, with gender balance via deterministic candidate search.
 age_bin=pd.qcut(pd.to_numeric(allp.age),4,labels=False,duplicates='drop'); group=allp.isocode.astype(str)+'|'+age_bin.astype(str)
 quotas=(group.value_counts().sort_index()*0.1); take=np.floor(quotas).astype(int); rem=100-take.sum(); order=(quotas-take).sort_values(ascending=False,kind='stable').index[:rem]; take.loc[order]+=1
 best=None; target=np.array([pd.to_numeric(allp.age).mean(),pd.to_numeric(allp.age).std(),pd.to_numeric(allp.gender).mean(),pd.to_numeric(allp.subj_math_skills).mean()]); scale=np.array([5,5,.1,1])
 for trial in range(200):
  rng=np.random.default_rng(SEED+trial); idx=[]
  for key,n in take.items():
   if n:idx.extend(rng.choice(np.flatnonzero(group.to_numpy()==key),n,replace=False))
  c=allp.iloc[idx]; stat=np.array([pd.to_numeric(c.age).mean(),pd.to_numeric(c.age).std(),pd.to_numeric(c.gender).mean(),pd.to_numeric(c.subj_math_skills).mean()]); score=np.sum(((stat-target)/scale)**2)
  if best is None or score<best[0]:best=(score,c.sort_values('id_gallup'))
 cohort=best[1].reset_index(drop=True); assert len(cohort)==100
 path=OUT/'data/sampled_participants.csv'
 if path.exists():
  old=pd.read_csv(path,dtype={'id_gallup':str});assert old.id_gallup.tolist()==cohort.id_gallup.tolist(),'Frozen sample changed'
 else:cohort.to_csv(path,index=False)
 rows=[]
 for field in ['age','gender','subj_math_skills','isocode']:
  if field=='isocode':
   for value in sorted(allp[field].unique()):rows.append(dict(variable=field,value=value,full_share=(allp[field]==value).mean(),sample_share=(cohort[field]==value).mean()))
  else:
   for label,frame in [('full',allp),('sample',cohort)]:rows.append(dict(variable=field,value=label,mean=pd.to_numeric(frame[field]).mean(),sd=pd.to_numeric(frame[field]).std()))
 pd.DataFrame(rows).to_csv(OUT/'data/sampling_distribution_report.csv',index=False)
 return cohort

def clean_json(raw):
 x=json.loads(raw.strip());assert isinstance(x,dict);return x

def sentence(s):return isinstance(s,str) and bool(s.strip()) and len(s.split())<=20 and bool(re.search(r'[.!?]$',s.strip()))

def validate1(raw,q,locked=None):
 x=clean_json(raw);assert set(x)=={'choice','reason'}
 choice=base.parse_answer(q,str(x['choice']));assert locked is None or choice==locked
 assert sentence(x['reason']);return choice,x['reason']

def validate2(raw):
 x=clean_json(raw);assert set(x)=={'context_influence','influence_reason'} and x['context_influence'] in {'yes','no','uncertain'}
 reason=x['influence_reason'];assert (reason is None if x['context_influence']=='no' else sentence(reason))
 return x['context_influence'],reason

def connect():
 p=OUT/'data/responses.sqlite3';db=sqlite3.connect(p,timeout=60)
 db.execute('CREATE TABLE IF NOT EXISTS records (person TEXT,arm TEXT,item TEXT,stage INTEGER,status TEXT,choice REAL,reason TEXT,raw TEXT,timestamp TEXT,attempts INTEGER,request_order INTEGER,error TEXT,PRIMARY KEY(person,arm,item,stage))');db.commit();return db

def put(db,person,arm,item,stage,status,choice,reason,raw,attempts,order,error=''):
 db.execute('INSERT OR REPLACE INTO records VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',(person,arm,item,stage,status,choice,reason,raw,datetime.now(timezone.utc).isoformat(),attempts,order,error));db.commit()

def messages(person,q,arm):
 m=base.persona_messages(person,q)
 if ARMS[arm]:m[0]['content']+='\n\n'+ARMS[arm]
 m[1]['content']+='\n\n'+STAGE1
 return m

def protocol(cohort):
 spec=json.loads((ARCH/'results/experiment.json').read_text())
 assert spec['temperature']==0 and spec['models']==[MODEL] and spec['calibration']==base.load_stakes()
 baseline,_=_read_model_block(ARCH/'results/conditions/baseline_repeat/replicate_001',MODEL,pd.read_csv(ARCH/'cohort.csv',dtype={'id_gallup':str}),spec)
 assert baseline is not None
 config={'seed':SEED,'sample_ids_sha256':hashlib.sha256('\n'.join(cohort.id_gallup).encode()).hexdigest(),'model':MODEL['id'],'temperature':0,'model_request_parameters':spec['model_request_parameters'][MODEL['id']],'baseline_protocol_sha256':spec['base_protocol_sha256'],'conditions':ARMS,'stage1':STAGE1,'stage2':STAGE2,'expected_stage_calls':12000,'sample_size':100}
 p=OUT/'config/experiment_config.json';text=json.dumps(config,indent=2,ensure_ascii=False)
 if p.exists():assert p.read_text()==text,'Frozen configuration changed'
 else:p.write_text(text)
 (OUT/'config/prompt_templates.json').write_text(json.dumps({'stage1':STAGE1,'stage2':STAGE2,'conditions':ARMS},indent=2))
 return spec,baseline

def run(limit=None, workers=10):
 cohort=sample();spec,baseline=protocol(cohort)
 settings=base.Settings.from_env(model=MODEL['id'],temperature=0)
 jobs=[(p,arm) for p in cohort.to_dict('records') for arm in ARMS]
 rng=np.random.default_rng(SEED);rng.shuffle(jobs)
 lock_path=OUT/'data/.run.lock'
 fd=os.open(lock_path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.write(fd,str(os.getpid()).encode());os.close(fd)
 counter=iter(range(1,1000000));counter_lock=threading.Lock();issued=[0]
 def next_order():
  with counter_lock:
   issued[0]+=1
   return next(counter)
 def job(pair):
  person,arm=pair;pid=person['id_gallup'];db=connect();client=base.ChatClient(settings,opener=curl_open);answers={}
  try:
   while (q:=base.next_question(answers,spec['calibration'])) is not None:
    m=messages(person,q,arm)
    for stage in (1,2):
     row=db.execute('SELECT status,choice,reason,raw,attempts FROM records WHERE person=? AND arm=? AND item=? AND stage=?',(pid,arm,q.key,stage)).fetchone()
     if row and row[0]=='valid':
      if stage==1:answers[q.key]=row[1]
      continue
     if stage==2:
      first=db.execute('SELECT choice,raw FROM records WHERE person=? AND arm=? AND item=? AND stage=1 AND status="valid"',(pid,arm,q.key)).fetchone();assert first is not None
      m2=m+[{'role':'assistant','content':first[1]},{'role':'user','content':STAGE2}]
     locked_choice=None
     for attempt in range(2):
      if limit and issued[0]>=limit:return
      request_messages=m if stage==1 else m2
      if attempt:
       request_messages=request_messages+[{'role':'assistant','content':raw},{'role':'user','content':('Repair the response format only. For Stage 1 return exactly two keys: choice and reason. Preserve the same choice if one was valid. The reason must be one complete sentence of no more than 20 words. Do not include context_influence or influence_reason.' if stage==1 else 'Repair the response format only. For Stage 2 return exactly two keys: context_influence and influence_reason. Do not include choice or reason. Do not revise the previous choice. If context_influence is no, set influence_reason to null; otherwise give one complete sentence of no more than 20 words.')}]
      order=next_order()
      try:
       payload=client.complete(request_messages);raw=payload['answer']
       if stage==1:
        ch,reason=validate1(raw,q,locked_choice);answers[q.key]=ch;put(db,pid,arm,q.key,stage,'valid',ch,reason,raw,attempt+1,order)
       else:
        influence,reason=validate2(raw);put(db,pid,arm,q.key,stage,'valid',None,json.dumps({'context_influence':influence,'influence_reason':reason}),raw,attempt+1,order)
       break
      except Exception as e:
       raw=locals().get('raw','')
       if stage==1 and locked_choice is None:
        try:locked_choice=base.parse_answer(q,str(clean_json(raw)['choice']))
        except Exception:pass
       put(db,pid,arm,q.key,stage,'invalid',locked_choice if stage==1 else None,None,raw,attempt+1,order,type(e).__name__)
       if attempt==1:break
     if stage==1 and q.key not in answers:break
    if q.key not in answers:break
  finally:db.close()
 try:
  if limit or workers==1:
   for pair in jobs:
    job(pair)
    if limit and issued[0]>=limit:break
  else:
   with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
    futures=[pool.submit(job,pair) for pair in jobs]
    for i,f in enumerate(concurrent.futures.as_completed(futures),1):
     f.result()
     if i%10==0:print('completed participant-arms',i,'of',len(jobs),'requests',issued[0],flush=True)
 finally:lock_path.unlink(missing_ok=True)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('command',choices=['check','run']);ap.add_argument('--max-requests',type=int);ap.add_argument('--workers',type=int,default=10);a=ap.parse_args()
 if a.command=='check':
  c=sample();protocol(c);print('sample',len(c),'expected calls',12000);return
 run(a.max_requests,a.workers)
if __name__=='__main__':main()
