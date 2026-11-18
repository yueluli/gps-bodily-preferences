# GPS1000：四组单独身体线索实验

使用归档同一批 1,000 个 GPS ID，学校网关 `gpt-6-luna`，每组每人 20 道自适应访谈题。baseline 从 `GPS1000_joint/archive/GPS1000_four_groups/results` 只读复用，不发送 baseline 请求。

| 条件 | 提示词 |
|---|---|
| sleep_mean | Last night you slept for 7 hours. |
| sleep_individual | Last night you slept for {逐人值} hours. |
| steps_mean | You have walked 4,961 steps today. |
| steps_individual | You have walked {逐人值} steps today. |

根据用户更正，四组统一使用昨晚睡眠／今天步数措辞，仅数值不同。旧措辞试跑隔离存放于 archive_mixed_wording，不纳入新分析；固定值组提示完全相同，其答案经校验后复用。分布值复用 `GPS1000_joint/distribution_source.csv` 的 `sleep_draw` 与 `steps_draw`，与 ID 一一对应，不重新抽样。这里的“一比一”指每个 GPS ID 固定一个模拟值，不代表外部受试者实测数据的逐人对应。千人包的分布赋值方法与原 100 人的人口分层赋值方法存在差异：原 100 人所用睡眠原始数据未随文件夹提供。两项身体线索始终分别输入。

## 运行

Python：`/Users/yueluli/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`

在项目根目录执行 `python GPS1000_single_cue/run.py check` 离线校验，`python GPS1000_single_cue/run.py run --workers 10` 运行或断点续跑，`python GPS1000_single_cue/run.py analyze` 刷新比较。已通过校验的答案自动保留。每个条件只有全部 1,000 人完整时才进入统计；四组全完成后自动绘图。`baseline_repeat` 虽登记于 manifest，但明确排除在 API 生成列表之外。

## 输出

- `assignments.csv`：固定到 ID 的数值。
- `prompts.jsonl`：4,000 条首题完整提示。
- `results/conditions/*/replicate_001/responses.sqlite3`：逐题断点和请求审计数据。
- `comparison/progress.csv`：完整访谈数。
- `comparison/combined_mse_comparison.csv`：各组六个偏好的 MSE、相对 baseline 的差及 95% 区间。
- `comparison/fixed_distribution_six_panels.png`、同名 PDF：与参考图片对应的六面板图。

沿用原计分函数和按条件标准化方法；比较每组与真人 GPS 的误差减去 baseline 与真人误差。负 ΔMSE 表示更接近真人。配对 bootstrap 为 1,000 次，种子 42，以当前生成结果和固定计分为条件；不将一次生成的不确定性全部解释为 prompt 效果。每组每人一次访谈，baseline 来自另一批调用。常数分数导致不可定义的指标保留 NA，不能擅自设成 0 或沿用旧图的 NA 结论。

## 执行记录

Material Passport: code experiment; requested four single-cue conditions; 1,000 paired participants; archived baseline; model gpt-6-luna; raw response audit stored locally; final completeness determined by protocol replay.
