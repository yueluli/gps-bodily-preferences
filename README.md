# GPS 身体提示与经济偏好实验

整理日期：2026-11-18。此文件是团队共享索引。

## 研究目的

检验加入睡眠、步数提示是否使模型模拟的六项经济偏好更接近 GPS 真人回答。每人每条件回答 20 道题，比较群体分布与逐人误差。

## 项目目录

| 目录 | 内容 |
| --- | --- |
| Bodily_standalone | 初始实验脚本、绘图及依赖说明 |
| bodily_assignments | 100 人固定值与分布赋值方法、参考数据 |
| gps100_luna_distribution | 100 人分布实验输出及比较总结 |
| GPS1000_joint | 千人联合平均、联合五档、逐人联合实验 |
| GPS1000_single_cue | 千人睡眠/步数单项固定值及分布实验、扩展分析 |
| GPS1000_apples | 苹果提示对照代码与运行输出；完成状态需进一步核验 |
| study1_rq1 | 六项偏好计分方法及分析 |

## 新成员阅读顺序

1. `bodily_assignments/README.md`：100 人赋值来源与方法。
2. `GPS1000_joint/README.md`：联合条件与千人赋值。
3. `GPS1000_single_cue/README.md`：单项实验、措辞修正和执行方法。
4. `GPS1000_single_cue/extended_analysis/中文结果说明.md`：扩展结果。
5. `study1_rq1/six_preferences_method.md`：计分方法。

## 必须保留的解释边界

- 固定值是睡眠 7 小时、步数 4,961 步；步数来自总体均值，不能称为中位数。
- “一比一”指每个 GPS ID 固定一个模拟值，不是该受访者的实测身体状态。
- 100 人与千人分布赋值方法不同，不能视为完全相同的重复实验。
- 单项实验旧措辞试跑保存在 archive_mixed_wording，不纳入新版分析。
- baseline 与新增条件可能来自不同调用批次；每人每条件单次生成限制因果解释。
- 结果必须对应具体批次、条件与报告，不能把某组误差推广到全部实验。

## 运行入口

在项目根目录，按各子目录 README 配置数据、Python 依赖和 API 环境变量后，先执行 `python GPS1000_joint/run.py check` 或 `python GPS1000_single_cue/run.py check`。`run` 会调用模型；`analyze` 刷新分析。复现依赖归档 baseline、冻结赋值和原始 GPS 数据，仅有脚本不能完整复现。

## GitHub 交付状态

私有仓库 `gps-bodily-preferences` 用于团队共享。本仓库只收录代码与说明；受访者级数据、请求日志、依赖缓存、重复压缩包和 API 凭据保留在本地。运行前需另行取得数据与凭据。
