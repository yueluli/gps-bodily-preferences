# GPS 100 人：睡眠和步数赋值

## 数值与来源

| 指标 | 参考数据的均值 | 参考数据的中位数 | 固定数值条件 |
|---|---:|---:|---:|
| 睡眠时长 | 7.0061 小时 | 7 小时 | 7 小时（原始数据按整小时记录） |
| 每日步数 | 4,961 步（论文报告的 717,527 人总体均值） | 公开资料未提供可核验的总体中位数 | 4,961 步 |

睡眠来源：Coutrot et al., *Nature Communications* (2022), [论文](https://www.nature.com/articles/s41467-022-34624-8)、[OSF 数据](https://osf.io/j7sd4/)。本地输入为 `C:\Users\Administrator\Downloads\j7sd4-osfstorage-archive.zip` 中的 `clean_demog_data.csv`，共 730,187 人；变量包括年龄、性别、国家和自报睡眠时长。

步数来源：Althoff et al., *Nature* (2017), [论文](https://www.nature.com/articles/nature23018)、[作者数据仓库](https://github.com/timalthoff/activityinequality/tree/master/data)。仓库中的国家×性别 P25/P50/P75、年龄×性别均值、111 国平均步数已复制到本项目 `reference_data/`。这些是汇总数据，不是个人逐日步数。论文报告的总体标准差为 2,684 步；公开表格不能准确还原总体中位数。

## 文件

- `gps100_constant_values.csv`：100 人固定睡眠 7 小时、固定步数 4,961 步；用于你的两组独立比较。
- `gps100_distribution_values.csv`：100 人各自的模拟睡眠与步数；供分布条件使用。
- `gps100_bodily_values.csv`：上述两组值及每人匹配层级、参考分位点，便于审核。
- `assignment_manifest.json`：输入文件哈希、随机种子和匹配统计。
- `make_assignments.py`：完整生成过程。运行命令：`python bodily_assignments/make_assignments.py`，需 `pandas`、`numpy`。

## 分布赋值规则

1. 使用 `GPS_导师100人名单.csv` 中固定的 `id_gallup`，不重新抽 GPS 人员。GPS 性别编码为 0=男、1=女。
2. 睡眠：从原始数据中按国家、性别、年龄段（19–33、34–53、54–70 岁）匹配，至少 30 人时随机抽取一条真实睡眠值；否则依次退回国家×性别或总体×性别×年龄段。GPS 年龄超出 19–70 岁时，使用最近的年龄段，并在表中标记。睡眠源国家代码为两位，GPS 为三位，代码中有明确映射。
3. 步数：有国家×性别分位点的，用 P25/P50/P75 拟合对数正态分布并抽样，再按年龄×性别平均步数调整；没有详细分位点但有国家均值的，以该国均值缩放总体性别分位点；剩余使用总体性别分位点。每行 `steps_match` 记录使用了哪一级信息。这是汇总数据生成的近似分布，不能声称是论文原始逐人步数。
4. 随机种子为 `20261110`。同一个 `id_gallup` 的值一次生成、各条件和重复运行都固定，不让模型自行编造睡眠或步数。

## 与 baseline 比较时的提示词变更

复用导师 baseline 的参与者资料、题目、模型和请求设置。每次只加一句，分别建立两个条件：

- 睡眠固定值：`You usually sleep 7 hours per night.`
- 步数固定值：`You take 4,961 steps on a typical day.`

分布条件把句中的数字替换为 `gps100_distribution_values.csv` 中该 `id_gallup` 的数值。五种条件（baseline、固定睡眠、固定步数、分布睡眠、分布步数）均用相同 ID 做配对分析；睡眠和步数不要混入同一条件，除非另设联合条件。提示词中的其他文字和题序必须一致。最终比较每人的六个偏好指标与真实 GPS 答案的误差，以及同一人相对 baseline 的模型输出差异。

**核对条件：** 这 100 个 ID 是导师代码及压缩包默认设置推算的；如导师实际运行时改了 `--participants`、`--seed`，或使用另一份 `cohort.csv`，先用实际输出的 `cohort.csv` 逐个核对，再运行实验。睡眠和步数值均为外部数据模拟状态，不是 GPS 参与者本人测量值。
