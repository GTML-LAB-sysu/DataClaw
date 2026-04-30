<div align="center">

<h1>DataClaw</h1>

<img src="logo.png" alt="DataClaw Logo" width="220"/>

<br/>
<br/>

[![🏆 Leaderboard](https://img.shields.io/badge/🏆_Leaderboard-DataClaw-red)](https://gtmllab.github.io/DataClaw/)
[![🤗 HuggingFace](https://img.shields.io/badge/🤗_HuggingFace-Dataset-yellow)](https://huggingface.co/datasets/GTMLLab/DataClaw)
![Tasks](https://img.shields.io/badge/Tasks-492-blue)
![Categories](https://img.shields.io/badge/Categories-7-green)

</div>

> 面向 OpenClaw 类端到端智能体的数据分析评测集，所有任务来自真实数据环境，且具备唯一客观答案。



[English README](README.md)

## 🌊 OpenClaw 时代的数据分析任务正在变化

随着 OpenClaw 一类端到端智能体的出现，数据分析任务已经不再等价于“读一段文本，再输出一个答案”的静态问答问题。真实世界中的数据分析任务往往要求智能体在异构文件中定位证据、跨表筛选与关联实体、执行统计与归一化计算、校验中间结果，并严格遵循输出约束。

这意味着评测基准的核心难点，已经从单一的答案生成，转向完整的智能体驱动执行。一个真正有价值的数据分析评测基准，不仅要考察最终答案是否正确，还要考察智能体是否能够在复杂数据环境中稳定完成检索、筛选、计算、验证与约束遵循等一系列步骤。

DataClaw 正是面向这一变化而设计。它评测的不是脱离执行环境的抽象能力，而是在真实数据条件、明确任务约束和可复现执行协议下，OpenClaw 类端到端智能体完成数据分析任务的实际表现。

## 🔍 DataClaw 是什么

DataClaw 是一个面向真实复杂数据环境的过程导向数据分析任务评测基准。核心目标并非仅仅是衡量智能体在数据分析任务上的最终表现，而是旨在将其作为一个现实高保真的测试平台，同时细粒度地评估智能体在面临真实复杂环境和多步推理时的演化过程。

DataClaw大规模地模拟了高噪声、弱语义、跨领域的真实世界数据环境。通过金融领域与计算机领域的人类专家撰写复杂数据分析任务问题，并由人类专家和AI辅助交叉核验提供每个任务的过程性标注和唯一客观答案。其中，过程性标注包括任务里程碑、人工订正参考轨迹和证据数据来源。DataClaw 采用 OpenClaw 作为统一 agent 框架。


## 🎯 为什么选择 DataClaw

- **从理想化的假设数据环境到非理想化的真实数据环境。** DataClaw 包含混合结构和非结构化数据，覆盖企业画像、企业经营状态、区域产业统计、全国行业统计与政策文本等资源。所有信息均来自真实世界采集，并面临指标缺失、口径不一致、命名不一致等摩擦；任务面对的是现实风格的数据环境，而非过度清洗后的单表查值。
- **从单点静态查询到多步动态推理。** DataClaw任务通常要求智能体完成多阶段操作链，而不是一次性命中答案。对 agent 的挑战不仅来自检索，更来自跨源整合、指标构造、聚合计算与格式约束执行。
- **从结果导向评估到过程导向评估。** DataClaw超越单纯的结果准确率评估，对智能体的运行演化过程进行解剖式评测。结果导向的评估范式仅关注最终准确率。这种黑盒方法忽视了中间推理过程，极大弱化了评测的优化指导意义。

## 🏗️ 本仓库代码架构


关键目录与脚本职责如下：

- `assets/database/`：评测数据文件，运行时会整体注入到容器工作区。根目录含 `internal_metrics.csv`（业务逻辑内部知识库）；`enterprise/`、`industry/`、`policy/` 为三大主题域数据。
- `assets/qa_raw/`：原始任务源文件。
- `assets/qa_gold/`：由 `qa_raw` 归约得到的精简 gold 文件。
- `tasks/`：生成后的 OpenClaw task 规范文件。
- `dataclaw/build_tasks.py`：从 `qa_raw` 生成 `qa_gold` 与 `tasks/` 的构建器。
- `dataclaw/eval/run_batch.py`：宿主机侧评测编排器，负责每任务独立容器执行。
- `dataclaw/utils/docker_utils.py`：容器生命周期管理、OpenClaw onboarding 与模型配置。
- `dataclaw/utils/grading.py`：结果评分（LLM-judge 计算 Acc）。
- `dataclaw/utils/process_grading.py`：过程评分（correct 任务计 EE；incorrect 任务计 GPR / TPE）。
- `script/docker_save_image.sh`：镜像构建与导出脚本。

### ⚙️ 评测执行生命周期

每个评测任务都在独立 Docker 容器中运行。宿主机编排器管理完整生命周期：

```text
宿主机 (dataclaw/eval/run_batch.py)
  |
  +-- 对每个任务（通过 --parallel N 并行）：
      1. docker run   -> 启动隔离容器
      2. docker cp    -> 注入工作区文件
      3. docker exec  -> OpenClaw onboard
      4. docker exec  -> 启动 gateway（后台）
      5. docker exec  -> 设置模型并运行 agent
      6. docker exec  -> 调用 llm_judge 评分
      7. docker cp    -> 收集日志与结果
      8. docker rm    -> 清理容器
```


## 🚀 使用者快速开始

### 1. 获取预构建镜像

从 Releases 下载预构建镜像压缩包并加载：

```bash
docker load -i <dataclaw-image-archive>.tar
```

加载后，请确认本地镜像 tag 与 `.env` 中的 `DOCKER_IMAGE` 一致。

### 2. 克隆本仓库

```bash
git clone <repository-url>
cd <repository-dir>
```

实际仓库地址请以当前 GitHub 页面为准。

### 3. 安装 Python 依赖

```bash
pip install pyyaml python-dotenv
```

> `pyproject.toml` 要求 Python `>=3.10`。如需更完整的本地开发环境，也可以按你的习惯额外安装开发依赖。

### 4. 配置环境

复制模板：

```bash
cp .env.example .env
```

编辑 `.env`，至少关注以下字段：

| 变量 | 必填 | 说明 |
| --- | --- | --- |
| `DEFAULT_MODEL` | 是 | 待评测主模型，例如 `openrouter/anthropic/claude-sonnet-4.6` |
| `OPENROUTER_API_KEY` | 二选一 | 当主模型或 Judge 通过 OpenRouter 调用时使用 |
| `OPENCLAW_CUSTOM_BASE_URL` + `OPENCLAW_CUSTOM_API_KEY` | 二选一 | 自定义 OpenAI-compatible API |
| `OPENCLAW_CUSTOM_MODEL_ID` | 否 | 自定义主模型在 provider 中的显式 model id |
| `JUDGE_MODEL` | 否 | Judge 模型，默认值见 `.env.example` |
| `JUDGE_CUSTOM_BASE_URL` + `JUDGE_CUSTOM_API_KEY` | 否 | Judge 使用独立自定义 endpoint 时填写 |
| `JUDGE_CUSTOM_MODEL_ID` | 否 | Judge 自定义 endpoint 的显式 model id |
| `DOCKER_IMAGE` | 否 | 本地镜像 tag，需与实际加载的镜像一致 |

#### 🔌 自定义 OpenAI-compatible API

如果不使用 OpenRouter，可以在 `.env` 中设置：

```bash
OPENCLAW_CUSTOM_BASE_URL=https://your-api-url/v1
OPENCLAW_CUSTOM_API_KEY=your_api_key
OPENCLAW_CUSTOM_MODEL_ID=your-provider/your-model
DEFAULT_MODEL=your-provider/your-model
```

如果 API 运行在宿主机上：

```bash
OPENCLAW_CUSTOM_BASE_URL=http://host.docker.internal:8000/v1
```

Judge 使用独立 endpoint 时：

```bash
JUDGE_CUSTOM_BASE_URL=https://your-judge-api-url/v1
JUDGE_CUSTOM_API_KEY=your_judge_api_key
JUDGE_CUSTOM_MODEL_ID=your-provider/your-judge-model
```

##### 主模型与 Judge 的常见认证组合

| 场景 | 主模型 | Judge | 所需配置 |
| --- | --- | --- | --- |
| A | 自定义 API | OpenRouter | `OPENCLAW_CUSTOM_*` + `OPENROUTER_API_KEY` |
| B | OpenRouter | OpenRouter | `OPENROUTER_API_KEY` |
| C | 自定义 API | 自定义 API（独立 endpoint） | `OPENCLAW_CUSTOM_*` + `JUDGE_CUSTOM_*` |

### 5. 运行评测

```bash
# 运行全部任务
python dataclaw/eval/run_batch.py --model openrouter/anthropic/claude-sonnet-4.6

# 运行指定任务
python dataclaw/eval/run_batch.py --model ... --suite task_001,task_002

# 并行运行
python dataclaw/eval/run_batch.py --model ... --parallel 4

# 运行单个任务文件
python dataclaw/eval/run_batch.py --task tasks/task_001_xxx.md

# 或使用便捷脚本（从 .env 读取 DEFAULT_MODEL）
bash script/run.sh
```

### CLI 选项

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--model` / `-m` | `.env` 中的 `DEFAULT_MODEL` | 待评测模型 |
| `--judge` | `.env` 中的 `JUDGE_MODEL` | Judge 模型 |
| `--suite` / `-s` | `all` | `"all"` 或逗号分隔的任务 ID |
| `--task` / `-t` | — | 单个 `task.md` 文件路径 |
| `--parallel` / `-p` | `1` | 并行容器数 |
| `--timeout-multiplier` | `1.0` | 缩放所有任务超时时间 |
| `--runs` | `1` | 每个任务的重复运行次数 |
| `--resume` | — | 从上次中断处恢复运行 |
| `--verbose` / `-v` | — | 启用详细日志 |

### 6. 结果

运行完成后，结果保存在 `output/<task_id>/<model_timestamp_runid>/` 下：

```text
output/<task_id>/<suffix>/
├── score.json               # 结果评分（Acc）
├── process_score.json       # 过程评分（EE / GPR / TPE）
├── usage.json               # token 统计、费用、耗时
├── agent.log                # agent 执行日志
├── gateway.log              # gateway 日志
├── chat.jsonl               # 完整对话记录
├── judge_chat.jsonl         # outcome-judge 对话
└── judge_process_chat.jsonl # process-judge 对话
```

全局汇总会写入：

```text
output/summary_<model>.json
```

### 7. 评分规则

DataClaw 对每次运行从 **四个指标** 打分。

| 指标 | 含义 | 计算范围 | 方向 |
| --- | --- | --- | --- |
| **Acc** | LLM-judge 评判预测答案 â 与标准答案 a 的语义一致性，含 L 个子问题时取归一化平均 | 全部任务 | ↑ |
| **EE** | 执行效率 = N / T（N=gold 参考步数，T=agent 实际步数）。EE>1 表示比 gold 更省步 | 仅 correct 任务 | ↑ |
| **GPR** | 目标进展率 = (1/M) Σⱼ 𝕀(mⱼ 达成)，agent 在轨迹中达成的里程碑占比，用于在答错时捕捉过程得分 | 仅 incorrect 任务 | ↑ |
| **TPE** | 时序进展效率 = (Σⱼ 𝕀(mⱼ) · γ^max(tⱼ−N, 0)) / Σⱼ 𝕀(mⱼ)，γ=0.9；对 agent 已达成的里程碑做时序衰减平均，N 步内达成贡献 1，之后按 γ 指数衰减。所有已达成里程碑均在第 N 步内达成时 TPE=1，越晚 TPE 越低。取值范围 [0, 1]。 | 仅 incorrect 任务 | ↑ |

### 8. 中断恢复

长时间的批量评测可能因意外而中断。评测框架会在每个任务完成后自动保存进度文件：

```text
output/progress_<model>.json
```

只需在原命令后加上 `--resume` 即可恢复：

```bash
# 原始运行（中途中断）
python dataclaw/eval/run_batch.py --model openrouter/anthropic/claude-sonnet-4.6 --suite all

# 恢复运行（其余参数保持一致）
python dataclaw/eval/run_batch.py --model openrouter/anthropic/claude-sonnet-4.6 --suite all --resume
```

恢复时，框架会自动校验 `--model`、`--suite`、`--runs` 是否与上次运行一致；若不一致，会直接报错退出。全部任务完成后，进度文件会被自动删除。

如需放弃之前的进度并重新开始，删除对应进度文件即可：

```bash
rm output/progress_<model>.json
```

### 9. 清理

如果运行被中断，可能会留下尚未清理的容器。可以按如下方式清理：

```bash
IMAGE=<your-docker-image-tag>
docker ps -a --filter "ancestor=${IMAGE}" -q | xargs -r docker rm -f
```

预览会被移除的容器：

```bash
IMAGE=<your-docker-image-tag>
docker ps -a --filter "ancestor=${IMAGE}" --format "{{.Names}}\t{{.Status}}"
```

## 📊 数据集统计信息

DataClaw数据并非来源于合成样本或教学示例，而是基于发布团队在中国企业、产业与政策研究中的长期一线数据积累与行业洞察。当前版本以 2022 年相关数据为主，经过必要脱敏处理后构建任务，尽可能避免模型知识泄露且保留真实业务中的信息噪声与数据摩擦。任务撰写与标注由中山大学岭南学院专业团队完成，兼顾学术规范与业务可用性。

### 🗂️ 数据环境统计信息

当前版本数据环境在主题域内，按业务口径归纳为 **3 个主题域**：**企业**、**产业**、**政策**；细分类目覆盖企业画像与分区画像、企业核心竞争力、经营状态、区域/全国产业统计、政策发布与政策原文等，贴近真实研究与咨询分析链路。3个主题域包含**17 个独立数据源**（每个数据文件计为一个数据源，统一挂载到 `assets/database/`）：其中 **17** 个按主题域归入子目录 `enterprise/`、`industry/`、`policy/`；另有 **1** 个根目录文件 `internal_metrics.csv`，作为**业务逻辑内部知识库**，不归属任一主题域。详细说明见下。

| 维度 | 统计值 | 说明 |
| --- | --- | --- |
| 主题域 | 3 | 企业、产业、政策 |
| 二级主题 | 7 | 企业 3（画像、核心竞争力、经营状态），产业 2（区域产业、全国行业），政策 2（发布情况、原文） |
| 数据源总数 | 17 | 运行时整体注入容器工作区 |
| 文件格式 | CSV | 以 CSV 为主；同时包含结构化字段与非结构化长文本型内容 |
| 时间跨度 | 主要集中于2022年 | 不同数据源统计周期不一致 |

**各主题域及二级主题下的 17 个数据源**

<table>
<thead>
<tr><th>主题域</th><th>二级主题</th><th align="right">数据源数量</th><th>数据文件</th></tr>
</thead>
<tbody>
<tr>
<td style="white-space:nowrap">企业</td>
<td style="white-space:nowrap">企业画像</td>
<td align="right">5</td>
<td><code>enterprise/company_profile.csv</code><br><code>enterprise/company_profile_as.csv</code><br><code>enterprise/company_profile_eu.csv</code><br><code>enterprise/company_profile_na.csv</code><br><code>enterprise/company_profile_oc.csv</code></td>
</tr>
<tr>
<td style="white-space:nowrap">企业</td>
<td style="white-space:nowrap">企业核心竞争力</td>
<td align="right">1</td>
<td><code>enterprise/company_core.csv</code></td>
</tr>
<tr>
<td style="white-space:nowrap">企业</td>
<td style="white-space:nowrap">企业经营状态</td>
<td align="right">3</td>
<td><code>enterprise/company_operation_status.csv</code><br><code>enterprise/company_operation_status_detail.csv</code><br><code>enterprise/company_operation_yearly_status.csv</code></td>
</tr>
<tr>
<td style="white-space:nowrap">产业</td>
<td style="white-space:nowrap">区域产业</td>
<td align="right">3</td>
<td><code>industry/regional_industry_status.csv</code><br><code>industry/regional_industry_status_detail.csv</code><br><code>industry/regional_industry_yearly_status.csv</code></td>
</tr>
<tr>
<td style="white-space:nowrap">产业</td>
<td style="white-space:nowrap">全国行业</td>
<td align="right">3</td>
<td><code>industry/national_industry_status.csv</code><br><code>industry/national_industry_status_detail.csv</code><br><code>industry/national_industry_yearly_status.csv</code></td>
</tr>
<tr>
<td style="white-space:nowrap">政策</td>
<td style="white-space:nowrap">政策发布情况</td>
<td align="right">1</td>
<td><code>policy/policy_release_status.csv</code></td>
</tr>
<tr>
<td style="white-space:nowrap">政策</td>
<td style="white-space:nowrap">政策原文</td>
<td align="right">1</td>
<td><code>policy/policy_resource.csv</code></td>
</tr>
</tbody>
</table>

> 在任务执行层面，智能体通常需要在多文件间完成实体对齐、跨表关联、口径归一与聚合计算，而非单文件查值；必要时还需结合 `internal_metrics.csv` 中的业务约定。这也是 DataClaw 用于评估真实场景数据理解与推理能力的核心价值。

### 📋 任务统计信息

当前版本共 492 个任务，覆盖 7 个类别；整体难度分布为 131 easy / 286 medium / 75 hard。

| 类别代码 | 含义 | 任务数 | 难度分布 |
| --- | --- | --- | --- |
| `enterprise_industry_analysis` | 企业-行业分析 | 226 | easy 115 / medium 111 |
| `enterprise_industry_policy_analysis` | 企业-产业-政策联动分析 | 76 | easy 10 / medium 66 |
| `comprehensive_decision` | 综合决策 | 70 | easy 6 / medium 45 / hard 19 |
| `international_comparison` | 国际比较 | 39 | medium 25 / hard 14 |
| `hypothesis_verification` | 假设验证 | 29 | medium 14 / hard 15 |
| `industry_planning` | 产业规划 | 28 | medium 14 / hard 14 |
| `risk_assessment` | 风险评估 | 24 | medium 11 / hard 13 |

> 除 `international_comparison` 的 39 个任务外，其余任务在当前 task 规范中都显式限制为仅使用 `./database/`，不依赖 web search。

## 🙏 致谢

DataClaw 由中山大学计算机学院陈川团队与南方周末科创力研究中心联合发布，真诚感谢南方周末科创力研究中心提供的宝贵数据和巨大支持。

同时，本项目构建在优秀的开源智能体生态系统之上。我们衷心感谢以下项目：

 [WildClawBench](https://github.com/InternLM/WildClawBench)

 [Claw-Eval](https://github.com/claw-eval/claw-eval)

 [PinchBench](https://github.com/pinchbench/skill)


