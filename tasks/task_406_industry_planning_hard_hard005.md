---
id: task_406_industry_planning_hard_hard005
name: industry_planning-hard-hard005
category: industry_planning
grading_type: llm_judge
timeout_seconds: 1200
gold_file: qa_gold/industry_planning/hard005.json
workspace_files: [
  {
    "source": "database/bilingual_translation_english_chinese.json",
    "dest": "database/bilingual_translation_english_chinese.json"
  },
  {
    "source": "database/enterprise/company_core.csv",
    "dest": "database/enterprise/company_core.csv"
  },
  {
    "source": "database/enterprise/company_operation_status.csv",
    "dest": "database/enterprise/company_operation_status.csv"
  },
  {
    "source": "database/enterprise/company_operation_status_detail.csv",
    "dest": "database/enterprise/company_operation_status_detail.csv"
  },
  {
    "source": "database/enterprise/company_operation_yearly_status.csv",
    "dest": "database/enterprise/company_operation_yearly_status.csv"
  },
  {
    "source": "database/enterprise/company_profile.csv",
    "dest": "database/enterprise/company_profile.csv"
  },
  {
    "source": "database/enterprise/company_profile_as.csv",
    "dest": "database/enterprise/company_profile_as.csv"
  },
  {
    "source": "database/enterprise/company_profile_eu.csv",
    "dest": "database/enterprise/company_profile_eu.csv"
  },
  {
    "source": "database/enterprise/company_profile_na.csv",
    "dest": "database/enterprise/company_profile_na.csv"
  },
  {
    "source": "database/enterprise/company_profile_oc.csv",
    "dest": "database/enterprise/company_profile_oc.csv"
  },
  {
    "source": "database/industry/national_industry_status.csv",
    "dest": "database/industry/national_industry_status.csv"
  },
  {
    "source": "database/industry/national_industry_status_detail.csv",
    "dest": "database/industry/national_industry_status_detail.csv"
  },
  {
    "source": "database/industry/national_industry_yearly_status.csv",
    "dest": "database/industry/national_industry_yearly_status.csv"
  },
  {
    "source": "database/industry/regional_industry_status.csv",
    "dest": "database/industry/regional_industry_status.csv"
  },
  {
    "source": "database/industry/regional_industry_status_detail.csv",
    "dest": "database/industry/regional_industry_status_detail.csv"
  },
  {
    "source": "database/industry/regional_industry_yearly_status.csv",
    "dest": "database/industry/regional_industry_yearly_status.csv"
  },
  {
    "source": "database/internal_metrics.csv",
    "dest": "database/internal_metrics.csv"
  },
  {
    "source": "database/policy/policy_release_status.csv",
    "dest": "database/policy/policy_release_status.csv"
  },
  {
    "source": "database/policy/policy_resource.csv",
    "dest": "database/policy/policy_resource.csv"
  }
]
---

## Prompt

云南省于2022年正式发布了绿色铝产业发展三年行动计划，其中载明了2024年绿色铝全产业链产值的量化目标。若以该省金属冶炼和压延加工业所有上市企业（仅覆盖中国大陆范围内的金属冶炼和压延加工业企业，不含港澳台数据））2022年的实际营业收入为基数，并假设各企业按自身现有增速（取全部上市企业营业收入同比增减幅的中位数作为统一测算基准）持续保持增长，经2年复合增长推算至2024年，请问：届时这些上市企业的营收汇总值与政策文件明确设定的产业链产值目标之间还存在多大缺口（以亿元计）？若要在2年内完全弥合上述缺口，在现有增速基础上还需年均额外拉升多少个百分点？

Output guidelines:
依次回答缺口金额和额外增速。缺口金额以亿元为单位，保留2位小数；额外增速以百分点为单位，保留2位小数。如[280.50, 4.12]。如果无法找到相关数据，请回答"未查询到相关数据"

Only use files under `./database/`.

## Expected Behavior

Agent should read the provided `database/` files, compute the result, and return the final answer. The final answer must follow the required output format.

## Grading Criteria

- [ ] Final answer semantically matches the gold `answer`.
- [ ] Output format follows `guidelines`.

## LLM Judge Rubric

### Criterion 1: Multi-answer Correctness (Weight: 100%)

Gold answer JSON:
`[356.36, 5.85]`

Scoring rules:
- The gold answer is a list with N=2 parts.
- Judge each predicted part against the corresponding gold part by semantic equivalence.
- Return `scores` with `part_0 ... part_1` each as 0 or 1.
- Return `total = (sum(part_i)) / 2` exactly.
- If the model output is missing or cannot be parsed into 2 comparable parts, score all parts 0.

