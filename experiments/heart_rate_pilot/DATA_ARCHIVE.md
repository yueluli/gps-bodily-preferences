# 完整实验数据归档

本仓库为公开仓库。以下分卷包含抽取的受访者 ID、人口背景、逐题模型原始回答、历史 baseline、真人参照、清洗数据、日志与分析输出，不含 API 密钥。

将 `full_experiment_data.zip.part01` 等分卷全部下载到同一目录，按文件名顺序拼接为 `full_experiment_data.zip`，再解压。可使用：

```python
from pathlib import Path
parts = sorted(Path(".").glob("full_experiment_data.zip.part*"))
Path("full_experiment_data.zip").write_bytes(b"".join(p.read_bytes() for p in parts))
```

`report/choices_and_reasons_zh.zip` 包含可筛选 HTML 表格与双语 CSV。中文理由目前仅完成 846/6000 条；其余明确标为待译，英文原文完整保留。

SHA256 (full_experiment_data.zip): `1319d1b1b900bebf8bcc24f04ab2ebf6edd48305ddb7e773ed6a13fd3e5094de`
