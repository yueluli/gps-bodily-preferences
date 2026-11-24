"""Build a local, searchable Chinese-labelled table with verbatim model outputs."""
from pathlib import Path
import csv,html,json
O=Path(__file__).resolve().parents[1];src=O/'data/combined_results.csv';out=O/'report/choices_and_reasons_zh.html'
labels={'will_to_take_risk':'风险承担意愿','will_to_giveup_today':'愿意为未来放弃眼前利益','punish_oneself':'不公平时自担成本惩罚','punish_others':'惩罚他人不公平行为','will_to_good_cause':'支持公益事业','will_to_return_favor':'回报他人帮助','will_to_ravenge':'报复意愿','trust':'信任他人','size_gift':'感谢礼物选择','hypo_donation':'意外所得捐赠金额'}
translations={
'The draw has a higher expected value than the sure payment.':'抽签的期望收益高于确定获得的金额。',
'I am fairly willing to support good causes without expecting anything in return.':'我比较愿意支持公益事业，而不期待回报。',
'I prefer the certainty of receiving 80 EUR over the risk of getting nothing.':'与可能一无所获相比，我更愿意确定拿到80欧元。',
'I prefer the guaranteed 160 EUR over a gamble with a lower expected value.':'我更愿意确定拿到160欧元，而不是参加期望收益更低的赌博。',
'I try to give people the benefit of the doubt while recognizing that intentions can vary.':'我愿意先信任别人，同时也知道每个人的意图可能不同。',
'I prefer the certainty of receiving 120 EUR over the risk of receiving nothing.':'与可能一无所获相比，我更愿意确定拿到120欧元。',
'I try to give people the benefit of the doubt, while recognizing that intentions can vary.':'我愿意先信任别人，同时也知道每个人的意图可能不同。',
'I prefer the certainty of receiving 80 EUR over the risk of receiving nothing.':'与可能一无所获相比，我更愿意确定拿到80欧元。',
'I generally feel willing to return favors when someone has helped me.':'有人帮助过我时，我通常愿意回报对方。',
'I prefer the certainty of receiving 120 EUR over the risk of getting nothing.':'与可能一无所获相比，我更愿意确定拿到120欧元。',
'I would prefer the larger payment in 12 months since there is no inflation.':'既然没有通胀，我更愿意在12个月后领取较大金额。',
'I would wait 12 months to receive the larger payment.':'我愿意等12个月，以获得较大金额。',
'I would donate a modest portion while keeping most of the unexpected money for personal needs.':'我会捐出一小部分，将大部分意外所得留作个人需要。',
'I prefer the certainty of receiving 40 EUR over the risk of getting nothing.':'与可能一无所获相比，我更愿意确定拿到40欧元。',
'I generally value reciprocity and am willing to return favors people do for me.':'我重视互惠，愿意回报别人对我的帮助。',
'I prefer the certainty of receiving 100 EUR over the risk of receiving nothing.':'与可能一无所获相比，我更愿意确定拿到100欧元。',
'I would wait a year to receive the larger payment.':'我愿意等一年，以获得较大金额。',
'I would prefer the substantially larger payment in 12 months.':'我更愿意在12个月后领取明显更大的金额。',
'I prefer receiving the money today rather than waiting a year for a small increase.':'与为少量增额等一年相比，我更愿意今天拿到钱。',
'I am generally willing to support good causes without expecting anything in return.':'我通常愿意支持公益事业，而不期待回报。'}
def choice_zh(q,c):
 if q.startswith('risk_'):return '50%抽签' if c=='1' else '确定金额' if c=='2' else c
 if q.startswith('patience_'):return '今天领取' if c=='1' else '12个月后领取' if c=='2' else c
 if q=='size_gift':return '不送礼物' if c=='1' else '选择第'+c+'档礼物'
 if q=='hypo_donation':return '捐赠 '+c+' 欧元'
 return c+' 分（原量表）'
rows=[]
with src.open(newline='') as f:
 for x in csv.DictReader(f):
  q=x['question_id'];name=labels.get(q,('风险抽签第'+q.split('_')[-1]+'题') if q.startswith('risk_') else ('耐心选择第'+q.split('_')[-1]+'题') if q.startswith('patience_') else q)
  rows.append({'id':x['participant_id'],'group':{'baseline_with_reason':'带理由 baseline','bodily_context':'静息心率 72','numerical_placebo':'非身体数字 72'}[x['condition']],'question':name,'qid':q,'choice':x['choice'],'choice_zh':choice_zh(q,x['choice']),'reason':x['reason'],'reason_zh':translations.get(x['reason'],'待译'),'context':{'yes':'是','no':'否','uncertain':'不确定'}.get(x['context_influence'],x['context_influence']),'influence_reason':x['influence_reason'] or '—'})
assert len(rows)==6000
payload=json.dumps(rows,ensure_ascii=False).replace('</','<\\/')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>心率实验：选择与理由</title><style>body{font:15px/1.5 system-ui,"PingFang SC",sans-serif;color:#20344f;background:#f6f8fb;margin:0;padding:28px}h1{margin:0 0 8px}.lead{color:#607086;margin-bottom:20px}.controls{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}input,select{padding:9px 12px;border:1px solid #c7d2df;border-radius:8px;background:white;font:inherit}.card{background:white;border:1px solid #dbe3ec;border-radius:12px;overflow:auto}table{border-collapse:collapse;width:100%;min-width:1250px}th,td{padding:10px 12px;border-bottom:1px solid #e6ebf0;text-align:left;vertical-align:top}th{position:sticky;top:0;background:#e9eff6}td:nth-child(6),td:nth-child(7){min-width:230px}.muted{color:#66788e}.pill{display:inline-block;border-radius:20px;background:#e4f4f1;padding:2px 8px}button{padding:8px 14px;border:0;border-radius:7px;background:#1f6386;color:#fff;cursor:pointer}.pager{margin-top:14px;display:flex;gap:12px;align-items:center}</style><h1>心率实验：原始选择与理由</h1><p class="lead">100 人 × 3 条件 × 20 题 = 6,000 条决策。原始选择与英文理由逐字保留。中文为阅读辅助；未译条目标注“待译”。此表只保存在本地。</p><div class="controls"><input id="search" placeholder="搜索参与者 ID、题目或理由" size="36"><select id="group"><option value="">全部条件</option><option>带理由 baseline</option><option>静息心率 72</option><option>非身体数字 72</option></select><select id="question"><option value="">全部题目</option></select><select id="translated"><option value="">全部译文状态</option><option value="yes">已翻译</option><option value="no">待译</option></select></div><p id="count" class="muted"></p><div class="card"><table><thead><tr><th>参与者 ID</th><th>条件</th><th>题目</th><th>原始选择</th><th>选择中文释义</th><th>原始英文理由</th><th>理由中文译文</th><th>自报受背景影响</th><th>自报原文</th></tr></thead><tbody id="body"></tbody></table></div><div class="pager"><button id="prev">上一页</button><span id="page"></span><button id="next">下一页</button></div><script id="data" type="application/json">'''+payload+'''</script><script>const rows=JSON.parse(document.getElementById('data').textContent),$=id=>document.getElementById(id),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));let current=0,filtered=rows;for(const q of [...new Set(rows.map(x=>x.question))]){$('question').insertAdjacentHTML('beforeend','<option>'+esc(q)+'</option>')}function render(){const term=$('search').value.trim().toLowerCase(),g=$('group').value,q=$('question').value,t=$('translated').value;filtered=rows.filter(x=>(!g||x.group===g)&&(!q||x.question===q)&&(!t||(t==='yes')===(x.reason_zh!=='待译'))&&(!term||[x.id,x.question,x.reason,x.reason_zh,x.choice].some(v=>String(v).toLowerCase().includes(term))));const pages=Math.max(1,Math.ceil(filtered.length/50));current=Math.min(current,pages-1);$('count').textContent=`匹配 ${filtered.length} 条；已译 ${filtered.filter(x=>x.reason_zh!=='待译').length} 条`;$('page').textContent=`第 ${current+1} / ${pages} 页`;$('body').innerHTML=filtered.slice(current*50,current*50+50).map(x=>`<tr><td>${esc(x.id)}</td><td>${esc(x.group)}</td><td>${esc(x.question)}</td><td><b>${esc(x.choice)}</b></td><td>${esc(x.choice_zh)}</td><td>${esc(x.reason)}</td><td class="${x.reason_zh==='待译'?'muted':''}">${esc(x.reason_zh)}</td><td>${esc(x.context)}</td><td>${esc(x.influence_reason)}</td></tr>`).join('')}for(const id of ['search','group','question','translated'])$(id).addEventListener(id==='search'?'input':'change',()=>{current=0;render()});$('prev').onclick=()=>{current=Math.max(0,current-1);render()};$('next').onclick=()=>{current++;render()};render();</script></html>'''
out.write_text(page)
print(out,'rows',len(rows),'translated',sum(x['reason_zh']!='待译' for x in rows))
