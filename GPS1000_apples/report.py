"""Render complete paired comparisons without changing the frozen scoring."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE = Path(__file__).resolve().parent
D = HERE / 'comparison'
p = pd.read_csv(D/'progress.csv')
if not (p.complete_interviews == 1000).all():
    raise SystemExit('Incomplete: no final report generated.')
s = pd.read_csv(D/'paired_raw_shifts.csv')
m = pd.read_csv(D/'combined_mse_comparison.csv')
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
a = s[s.comparison.isin(['sleep_mean minus baseline','apples_7 minus baseline'])]
a.pivot(index='item',columns='comparison',values='fraction_changed').plot.barh(ax=axes[0])
axes[0].set_xlabel('Fraction of paired participants with changed score')
axes[0].set_ylabel('Raw score component')
m.pivot(index='preference',columns='condition',values='delta_mse').plot.barh(ax=axes[1])
axes[1].axvline(0,color='black',lw=.8)
axes[1].set_xlabel('MSE minus baseline MSE (negative = closer to humans)')
fig.tight_layout()
fig.savefig(D/'apples_sleep_baseline.png',dpi=180)
fig.savefig(D/'apples_sleep_baseline.pdf')
text='''# Material Passport

Code experiment; 1,000 paired GPS personas; gpt-6-luna; apples condition newly generated; baseline and sleep_mean reused without new calls. Human GPS outcomes are scoring references, not model inputs.

# 苹果、睡眠与 baseline 对比

三组使用同一批 1,000 人，20 道题及原有模型参数。苹果组追加 `You have 7 apples.`；睡眠组追加 `Last night you slept for 7 hours.`；baseline 不追加。每题只发送人物设定、当组线索和当前题目。

比较文件：`paired_raw_shifts.csv` 报告三组两两配对的原始分数变化、绝对变化、变化比例及均值差的 95% 配对 bootstrap 区间；`combined_mse_comparison.csv` 报告各组与真人的 MSE 相对 baseline 的差。Bootstrap 为 1,000 次，种子 42。

苹果与 baseline 的差用于考察这一非身体信息提示是否也导致偏移；睡眠与苹果的直接比较用于描述两类信息的差异。单一苹果对照不能代表所有普通 prompt 改动；苹果还可能唤起食物或拥有物的联想。不同调用批次、每人每组一次生成，意味着结果不能单独排除生成波动，也不能把全部差异归因于身体信息。分数按既有流程标准化；原始回答变化是本问题的重要补充。

## 完整性

'''+p.to_csv(index=False)+'\n## 相对 baseline 的 MSE 差\n\n'+m.to_csv(index=False)
(D/'report.md').write_text(text)
print(D/'report.md')
