# Heart Rate Context Experiment

请基于当前项目已有的实验代码、1000名模拟参与者、之前的Baseline实验结果，以及原始paper中的真人经济决策数据，建立一个独立的Heart Rate Context Pilot Experiment。

## 1. Research Objective

本次实验旨在研究：

1. 加入静息心率信息是否会改变LLM模拟的人类经济决策。
2. 加入静息心率信息是否能够提高LLM与真人经济决策数据的一致性。
3. 这种变化究竟与身体语义（Bodily Semantics）有关，还是与单纯的数字信息（Numerical Anchoring）有关。
4. LLM是否会主动将身体信息纳入其决策解释。
5. LLM是否会在被询问时报告额外背景信息对其决策产生了影响。

本实验只研究心率，不加入睡眠、步数、饥饿、疲劳或其他身体数据。

## 2. Participant Sampling

从之前已经生成并完成Baseline实验的1000名参与者中抽取100人。

具体要求：

- 使用固定随机种子：random_seed = 42。
- 使用基于原始人口统计分布的分层随机抽样。
- 对原本近似正态分布的连续变量，例如年龄，按照原始分布进行分层抽样，使抽取的100人尽可能保持原始1000人的均值、标准差及分布形态。
- 对非正态分布的变量保留其原始分布，不强制转换为正态分布。
- 对性别、国家、教育程度等实际存在的分类变量，尽可能保持原始样本比例。
- 如果多变量联合分层导致样本过于稀疏，使用适当的边际分布平衡抽样方法。
- 不得根据参与者的经济偏好、历史选择、预测准确率或与真人数据的相似程度进行抽样。
- 保留原始participant_id和全部原始人口背景信息。
- 不生成新的persona。
- 所有LLM实验条件必须使用完全相同的100名参与者。
- 保存最终抽取的100名参与者名单。
- 输出100人样本与原始1000人的人口统计分布对比。

## 3. Experimental Conditions

设置以下五个条件，其中三个为新运行的LLM实验条件，另外两个为已有的参考数据。

### Condition A: Original Baseline

使用之前已经运行过的Baseline实验结果。

根据participant_id和question_id，从已有数据中提取本次抽取的100名参与者对应的所有经济决策结果。

不重新运行，不修改原始数据。

Condition ID:

`baseline_original`

### Condition B: Bodily Context

在原始Baseline Prompt中增加以下内容：

```text
You are seated and resting. Your current heart rate is 72 beats per minute.
```

严格保留该句，不得修改措辞。

不得增加对心率的解释，例如：

- Your heart rate is normal.
- You are calm.
- You are relaxed.
- You are healthy.
- Your heart rate indicates low stress.

模型应当自行理解心率信息，不主动引导其产生任何特定的情绪、性格或经济偏好。

Condition ID:

`bodily_context`

### Condition C: Numerical Placebo

保留原研究设计文档中的Matched Numbers设定，在与Bodily Context相同的位置增加：

```text
You are seated and resting. A nearby sheet records 72 as its final reference number.
```

严格保留该句，不得修改措辞。

该条件保留：

- 相同的数字72。
- 相同的坐姿及休息状态。
- 相同的背景信息插入位置。

但是数字72不具有身体或生理含义。

不要向模型解释该数字的实验用途，也不要告诉模型这是Placebo Condition。

Condition ID:

`numerical_placebo`

### Condition D: Baseline with Reason

使用与Original Baseline相同的人口背景、经济任务和原始Prompt。

不加入任何额外的身体信息、心率信息、参考数字或休息状态描述。

仅增加与Bodily Context和Numerical Placebo完全相同的两阶段输出要求。

设置该条件的目的是控制新增Reason输出要求可能对经济决策产生的影响。

如果Original Baseline已经使用完全相同的两阶段输出要求，则可以直接复用；否则需要重新运行。

Condition ID:

`baseline_with_reason`

### Condition E: Human Data

使用原始paper及其对应公开数据集中的真人经济决策结果作为Human Reference。

Condition ID:

`human_reference`

不要使用LLM生成或补充真人数据。

如果模拟参与者与真实参与者存在经过验证的一一对应关系，则根据原始ID进行匹配。

如果不存在一一对应关系，则在原始研究支持的国家、人口群体、问题或经济偏好维度上进行比较。

不得虚构个体匹配关系。

如果paper仅提供标准化偏好指数或汇总统计结果，则只进行这些数据所支持的比较，不得推断不存在的原始决策数据。

## 4. Experimental Controls

除实验条件规定的额外Prompt和统一输出格式之外，其他实验设置必须与之前的Baseline实验保持一致。

包括：

- Model name
- Model version
- System prompt
- Original demographic profile
- Economic decision tasks
- Question wording
- Answer options
- Question order
- Original branching logic
- Temperature
- Top-p
- Sampling parameters
- Reasoning effort
- Original decision protocol

Bodily Context和Numerical Placebo的额外信息必须插入原始Prompt中的相同位置。

不得在模型可见的Prompt中出现以下信息：

- Experimental condition labels
- Research hypotheses
- Human ground truth
- Historical baseline decisions
- Expected behavioral changes
- Numerical anchoring
- Placebo
- Prediction accuracy
- The purpose of adding heart rate information

不得根据实验结果调整Prompt、心率值、数字值或参与者样本。

## 5. Two-stage Response Protocol

对于每一名参与者的每一道经济决策问题，采用两阶段输出机制。

三个新运行条件必须使用完全相同的输出机制。

### Stage 1: Decision and Spontaneous Reason

在原始经济决策Prompt末尾增加以下指令：

```text
Make your decision based on the information provided.

First, provide your choice. Then, briefly explain the main reason for your choice in one complete sentence of no more than 20 words.

Return only valid JSON using the following format:

{
  "choice": "<your choice>",
  "reason": "<one brief sentence>"
}
```

输出示例：

```json
{
  "choice": "A",
  "reason": "I prefer a guaranteed outcome over an uncertain reward."
}
```

具体要求：

- Choice必须使用原始任务要求的合法答案格式。
- 如果原始任务要求A/B选项，则保留A/B。
- 如果原始任务要求数值、金额或资源分配，则保留相应的数据类型。
- Reason必须为一个完整的英文句子。
- Reason最多20个英文单词。
- 不输出详细推理过程。
- 不输出额外解释或其他JSON字段。
- 不主动提醒模型考虑心率、身体状态或数字72。
- 不要求模型解释新增条件的影响。
- 不要求模型必须使用全部背景信息。

Stage 1的目的是观察模型在自然做出决策的情况下，是否会主动将身体信息或数字信息纳入其决策解释。

完成Stage 1后，立即保存并锁定choice和reason。

后续步骤不得修改已经保存的choice。

### Stage 2: Self-reported Contextual Influence

在Stage 1完成之后，使用同一conversation发送独立的follow-up prompt。

```text
Did any contextual information beyond the economic decision itself influence your choice?

If yes, briefly identify the information and explain its influence in one sentence of no more than 20 words.

If you are uncertain, briefly explain why.

Do not revise your previous choice.

Return only valid JSON using the following format:

{
  "context_influence": "yes, no, or uncertain",
  "influence_reason": "<one brief sentence or null>"
}
```

可能的输出示例：

Example 1:

```json
{
  "context_influence": "yes",
  "influence_reason": "My resting heart rate suggested a calm physical state."
}
```

Example 2:

```json
{
  "context_influence": "no",
  "influence_reason": null
}
```

Example 3:

```json
{
  "context_influence": "uncertain",
  "influence_reason": "I cannot determine whether the additional contextual information affected my decision."
}
```

具体要求：

- context_influence只允许三个值：yes、no、uncertain。
- 如果回答yes，必须简短说明哪些背景信息产生了影响，以及如何影响决策。
- 如果回答no，influence_reason设置为null。
- 如果回答uncertain，可以简短解释原因。
- influence_reason最多20个英文单词。
- 不直接询问心率或数字72是否影响了选择。
- 不向模型提供新的背景信息。
- 不允许模型修改Stage 1的选择。
- 不在Stage 1中提前展示Stage 2的问题。
- 所有新运行条件必须使用完全相同的Stage 2 Prompt。

Stage 2必须是独立的API调用，而不是与Stage 1合并为一次调用。

Stage 2的回答仅作为探索性的自我报告数据，不视为模型真实内部决策机制的证据。

## 6. Conversation Management

对于每一道独立的经济决策问题：

1. 创建新的conversation。
2. 加载原始人口背景。
3. 加载对应的实验条件Prompt。
4. 加载原始经济决策问题。
5. 执行Stage 1。
6. 保存并锁定choice和reason。
7. 在同一个conversation中执行Stage 2。
8. 保存context_influence和influence_reason。
9. 结束当前conversation。

不同经济决策之间不得传递Stage 2内容。

如果原始经济任务存在adaptive questions或branching logic，则必须保留原始分支规则。

仅将原始任务所需的决策信息传递至后续问题，不得将Stage 2的自我报告内容传入后续决策。

在不同参与者和实验条件之间随机化API调用顺序，减少运行时间和服务端变化带来的系统性影响。

保存完整运行顺序与时间戳。

## 7. Data Validation

对每一次API输出执行自动验证。

Stage 1检查：

- 是否为合法JSON。
- 是否包含choice和reason。
- choice是否符合原始任务的合法答案范围。
- reason是否为空。
- reason是否为一个完整句子。
- reason是否超过20个英文单词。
- 是否包含未经允许的额外字段。

Stage 2检查：

- 是否为合法JSON。
- context_influence是否为yes、no或uncertain。
- influence_reason是否符合对应规则。
- influence_reason是否超过20个英文单词。

对于格式错误：

- 保存原始输出。
- 记录错误类型。
- 允许一次统一的格式修复重试。
- 不得根据Human Data或Original Baseline修改答案。
- 不得因为经济选择不符合预期而重新生成。
- 如果Stage 1的choice合法且可明确解析，但reason格式不合法，保留原始choice，不允许通过格式修复改变choice。
- 如果重试后仍然无效，标记为invalid。

分别报告首次输出有效率和最终有效率。

## 8. Data Storage

建立独立实验目录：

```text
experiments/heart_rate_pilot/
```

建议目录结构：

```text
experiments/heart_rate_pilot/
    config/
        experiment_config.json
        prompt_templates.json

    data/
        sampled_participants.csv
        sampling_distribution_report.csv
        baseline_original.csv
        baseline_with_reason.csv
        bodily_context_results.csv
        numerical_placebo_results.csv
        human_reference.csv
        combined_results.csv

    analysis/
        descriptive_statistics.csv
        prediction_accuracy.csv
        paired_comparisons.csv
        reason_analysis.csv
        reason_codebook.json
        context_influence_analysis.csv

    figures/

    logs/

    scripts/

    report/
        experiment_report.md
```

每一次经济决策至少保存以下字段：

```text
participant_id
condition
question_id
economic_domain
demographic_profile
original_question
original_answer_options
additional_context
choice
reason
context_influence
influence_reason
model_name
model_version
temperature
run_id
random_seed
timestamp
stage1_raw_response
stage2_raw_response
stage1_valid
stage2_valid
retry_count
error_type
```

Original Baseline不存在的reason和context_influence字段使用null。

Human Data中不存在的reason和context_influence字段同样使用null。

不得为历史Baseline或Human Data生成虚构的解释。

保存原始API输出和清洗后的结构化数据。

不要覆盖、删除或修改之前的任何实验结果。

## 9. Quantitative Analysis

沿用原始项目和原始paper中的经济偏好计算方式、标准化方法及评价指标。

不得在看到实验结果后修改评价方法。

主要比较以下五组：

1. Original Baseline
2. Baseline with Reason
3. Bodily Context
4. Numerical Placebo
5. Human Data

### 9.1 Descriptive Statistics

分别计算每个条件在各个经济偏好维度中的：

- Mean
- Median
- Standard deviation
- Choice distribution
- Sample size
- Missing rate
- Invalid response rate

根据当前项目中的实际经济偏好维度进行分析。

如果原始项目基于Global Preferences Survey，则保留原始六个维度：

- Risk-taking
- Patience
- Positive reciprocity
- Negative reciprocity
- Altruism
- Trust

不要自行增加或修改经济偏好维度。

### 9.2 Prediction Accuracy

分别比较：

```text
Original Baseline vs Human Data

Baseline with Reason vs Human Data

Bodily Context vs Human Data

Numerical Placebo vs Human Data
```

沿用原始paper已经使用的评价指标。

如果数据支持，可以同时报告：

- Mean Absolute Error
- Root Mean Squared Error
- Pearson correlation
- Spearman correlation
- R-squared
- Distributional distance

所有指标必须根据实际数据结构选择。

如果Human Data只包含国家层面或群体层面数据，不得计算虚假的个体层面预测准确率。

如果使用标准化经济偏好指数，保持所有条件的评分尺度可比较。

不得利用Human Data拟合或校准LLM输出。

### 9.3 Paired Condition Comparisons

使用相同参与者、相同问题的配对数据比较：

```text
Bodily Context vs Baseline with Reason

Numerical Placebo vs Baseline with Reason

Bodily Context vs Numerical Placebo

Baseline with Reason vs Original Baseline
```

计算：

- Choice change rate
- Direction of change
- Magnitude of change
- Effect size
- 95% confidence interval

根据原始任务的数据类型选择合适的配对统计方法。

对于二分类选择，可考虑McNemar检验。

对于连续数值或偏好指数，可考虑配对检验或participant-level bootstrap。

同一参与者存在多个决策时，考虑participant-level clustering。

对于多个经济偏好维度的统计检验，使用适当的多重比较校正。

### 9.4 Predictive Improvement

对于数值越低越好的误差指标，计算：

```text
Bodily Improvement =
Error(Baseline with Reason, Human Data)
- Error(Bodily Context, Human Data)
```

```text
Placebo Improvement =
Error(Baseline with Reason, Human Data)
- Error(Numerical Placebo, Human Data)
```

```text
Bodily-specific Improvement =
Error(Numerical Placebo, Human Data)
- Error(Bodily Context, Human Data)
```

正值表示对应实验条件更加接近真人数据。

对于相关系数等数值越高越好的指标，使用相应的反向定义。

分别报告：

- Overall improvement
- Improvement by economic preference dimension
- Improvement by demographic group（样本量允许时）
- Confidence intervals

Historical Original Baseline作为参考结果。

Baseline with Reason作为新实验的主要Baseline，以控制输出Reason这一操作可能产生的影响。

## 10. Reason Analysis

对三个新运行条件中的Stage 1 Reason进行探索性文本分析：

- Baseline with Reason
- Bodily Context
- Numerical Placebo

保留所有原始Reason。

建立统一的multi-label coding scheme。

初始编码类别包括：

```text
economic_payoff
risk_and_uncertainty
loss_avoidance
time_preference
fairness
altruism
reciprocity
trust
personal_background
bodily_state
heart_rate
calmness
stress
health
emotional_state
numerical_reference
explicit_72
other_context
other
```

编码要求：

- 一个Reason可以具有多个标签。
- 不强制每个Reason只归入一个类别。
- 根据文本中实际表达的内容进行编码。
- 不推测文本中未明确表达的隐藏动机。
- 在编码时尽可能隐藏实验条件标签。
- 不将编码分析结果反馈至实验Prompt。
- 保存编码标准、编码方法及每条Reason的编码结果。
- 区分关键词统计和语义编码结果。
- 如果使用LLM进行编码，使用统一的编码Prompt和固定模型配置，并抽取部分样本进行人工验证。

重点比较：

1. 各条件中主动提及身体状态的比例。
2. 各条件中主动提及心率的比例。
3. 各条件中主动提及数字72的比例。
4. 各条件中主动提及冷静、压力、健康或情绪的比例。
5. 各条件中主要使用经济收益、风险、时间或公平性解释决策的比例。
6. 相同参与者在相同问题中的choice与reason是否同时发生变化。
7. 即使choice没有变化，reason是否发生变化。

不要将模型生成的Reason视为其真实内部推理过程。

## 11. Contextual Influence Analysis

对Stage 2的自我报告结果进行独立分析。

分别计算各实验条件中：

- context_influence = yes的比例。
- context_influence = no的比例。
- context_influence = uncertain的比例。
- 在回答yes时，提及身体状态的比例。
- 在回答yes时，提及心率的比例。
- 在回答yes时，提及数字72的比例。
- 在回答yes时，提及人口背景或其他情境信息的比例。

进一步分析以下关系。

### 11.1 Spontaneous Reason vs Self-report

比较：

- Stage 1主动提及心率，Stage 2报告受到影响。
- Stage 1未提及心率，Stage 2报告受到心率影响。
- Stage 1主动提及身体状态，Stage 2报告没有受到额外背景影响。
- Stage 1与Stage 2均未提及身体状态。

对Numerical Placebo中的数字72执行对应分析。

### 11.2 Behavioral Change vs Self-reported Influence

以Baseline with Reason作为主要对照。

对于每个participant_id和question_id，检查Bodily Context及Numerical Placebo中的choice是否与Baseline with Reason不同。

将结果划分为：

```text
Choice changed + Reported influence

Choice changed + Reported no influence

Choice unchanged + Reported influence

Choice unchanged + Reported no influence
```

单独报告uncertain的结果。

对连续型决策同时报告变化幅度，避免只使用二元的changed/unchanged指标。

分析这些类别在不同经济偏好维度中的分布。

注意：

单次配对选择的差异可能来自随机生成，而不一定来自实验条件。

如果发现模型报告没有受到影响，但选择与Baseline不同，不得直接将其解释为无意识影响。

应描述为行为差异与模型自我报告之间的不一致。

实验条件层面的因果比较应基于整体统计结果，而不是单次生成的差异。

## 12. Visualization

生成统一风格、适合学术研究报告的可视化。

### Figure 1: Participant Sampling

展示：

- 原始1000人的人口统计分布。
- 抽取的100人的人口统计分布。
- 年龄、性别、国家、教育程度等实际存在的变量。

### Figure 2: Economic Preference Comparison

比较五组数据：

- Human Data
- Original Baseline
- Baseline with Reason
- Bodily Context
- Numerical Placebo

分别展示各经济偏好维度的结果。

仅在所有条件使用可比较尺度时绘制同一坐标轴上的对比。

### Figure 3: Prediction Error

展示四个LLM条件与Human Data之间的预测误差。

### Figure 4: Predictive Improvement

展示：

- Bodily Context相对于Baseline with Reason的改善。
- Numerical Placebo相对于Baseline with Reason的改善。
- Bodily Context相对于Numerical Placebo的改善。

添加95% confidence intervals。

### Figure 5: Decision Change

展示同一参与者在不同实验条件下的选择变化比例和方向。

### Figure 6: Spontaneous Reason Analysis

展示三个新运行条件中各Reason类别的出现频率。

突出比较：

```text
Bodily State
Heart Rate
Numerical Reference
Calmness
Stress
Economic Reasoning
```

### Figure 7: Self-reported Contextual Influence

使用堆叠柱状图展示三个新运行条件中的：

```text
Yes
No
Uncertain
```

### Figure 8: Behavioral Change and Self-report

展示实际观察到的Choice Change与Self-reported Influence之间的关系。

所有图表保存为：

- PNG
- SVG或PDF矢量格式

同时保存用于生成图表的原始统计数据。

## 13. Technical Implementation

首先检查当前repository：

1. 定位原始1000名参与者数据。
2. 定位之前的Baseline结果。
3. 定位原始实验Prompt。
4. 定位原始经济决策任务。
5. 定位模型调用配置。
6. 定位原始paper及对应的Human Data。
7. 定位已有的评价指标和分析函数。

尽可能复用现有代码，不要重新实现已经存在且有效的功能。

不要假设文件路径、字段名称或数据结构。

以实际repository内容为准。

在运行正式实验之前：

- 完成数据完整性检查。
- 检查participant_id与question_id是否可以正确匹配。
- 检查原始Baseline配置是否仍然可复现。
- 检查Human Data的实际可用层级。
- 检查所有实验Prompt之间的差异。
- 检查两个阶段的JSON解析。
- 检查choice数据类型。
- 检查branching logic。
- 检查断点续跑功能。
- 估算API调用数量和成本。

先使用少量测试记录进行technical dry run，仅验证代码、Prompt、JSON格式和数据保存流程。

不得依据dry run的经济选择或预测准确率优化实验Prompt。

技术验证完成后冻结：

```text
Participant sample
Experimental prompts
Model configuration
Response format
Evaluation metrics
Analysis procedure
```

如果存在关键数据缺失、模型版本不一致或无法恢复原始实验配置，应明确记录问题，不得凭空补齐。

如果模型版本与Original Baseline不同，应将历史Baseline明确标记为历史参考，而不是严格可控的同版本实验条件。

在正式批量API运行前输出预计调用次数及成本，避免未经确认的大规模付费调用。

## 14. Execution Requirements

实现完整可复现的实验运行流程。

支持：

- Fixed random seed
- Configuration file
- API rate-limit handling
- Retry mechanism
- Checkpointing
- Resume interrupted runs
- Duplicate request prevention
- Structured logging
- Data validation
- Progress tracking

API密钥使用环境变量或当前项目已有的安全配置。

不得将API密钥写入代码、日志或公开文件。

为每个实验条件建立独立的结果文件。

保存每个参与者、问题及阶段的运行状态。

重新运行时自动跳过已经成功完成的记录。

Stage 1成功而Stage 2失败时，只重试Stage 2，不重新生成Stage 1的经济选择。

## 15. Final Report

生成一份结构清晰的Markdown实验报告。

报告包括：

### 1. Research Objective

介绍研究问题和实验目的。

### 2. Experimental Design

说明五个对比条件、参与者抽样方式以及两阶段输出机制。

### 3. Sample Characteristics

比较抽取的100人与原始1000人的人口统计分布。

### 4. Economic Decision Results

报告各条件的经济决策结果及各偏好维度的差异。

### 5. Prediction Accuracy

比较各LLM条件与Human Data之间的一致性。

### 6. Bodily Semantics vs Numerical Anchoring

分析Bodily Context是否比Numerical Placebo产生更明显的预测改善。

### 7. Spontaneous Reason Analysis

分析模型是否主动使用心率、身体状态或数字72解释决策。

### 8. Self-reported Contextual Influence

分析模型是否报告受到额外背景信息的影响，以及其报告的影响来源。

### 9. Behavioral and Verbal Alignment

分析实际观察到的行为差异与模型自我报告之间的一致性。

### 10. Limitations

至少讨论以下限制：

- 100人样本属于pilot study。
- 固定心率72 bpm并非参与者实际测量的身体数据。
- 72 bpm是具有国际人口统计背景的参考值，而不是经过验证的全球算术平均心率。
- Bodily Context可能改变模型推断的临时身体状态，也可能改变其对参与者身份、健康状况或性格的推断。
- Numerical Placebo控制了数字72及部分情境，但不能排除全部语言语义和措辞差异。
- 新增Reason输出要求可能影响经济决策。
- Reason及Self-reported Influence不能证明模型的真实内部决策机制。
- 单次生成之间的选择变化可能来自随机性。
- Human Data的可用粒度可能限制个体层面的比较。
- Bodily Context与Numerical Placebo的差异不能直接证明LLM具有真实身体体验。

### 11. Conclusion

根据实际结果回答：

- 身体信息是否改变了LLM经济决策？
- 身体信息是否提高了LLM模拟真人经济决策的准确率？
- Bodily Context是否优于Numerical Placebo？
- 模型是否主动使用身体信息解释经济决策？
- 模型报告的背景信息影响是否与观察到的行为差异一致？

不预设任何正向结果。

完整报告正向、负向、无明显差异及统计不确定的结果。

## 16. Final Deliverables

最终提供：

1. 完整实验代码。
2. 可复现的实验配置。
3. 固定的100名参与者样本。
4. 所有实验条件的原始输出。
5. 清洗后的结构化数据。
6. 定量统计分析结果。
7. Reason编码结果。
8. Self-reported Contextual Influence分析结果。
9. 全部可视化图表。
10. Markdown实验报告。
11. README，包含环境配置、运行方式、断点续跑方式及结果文件说明。

请先检查当前repository及已有数据，随后实现完整实验流程。保持之前的实验代码和数据不变，将本次实验作为独立的Heart Rate Pilot Experiment进行管理。