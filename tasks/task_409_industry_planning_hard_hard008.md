---
id: task_409_industry_planning_hard_hard008
name: industry_planning-hard-hard008
category: industry_planning
grading_type: llm_judge
timeout_seconds: 1200
gold_file: qa_gold/industry_planning/hard008.json
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

以2022年为基期，针对中国大陆通用设备制造业设计双情景对比测算框架（通用设备制造业在册企业数量不少于5家的中国大陆省份，港澳台不纳入）。情景一（政策分化情景）：已出台制造业高质量发展省级专项文件的省份，其通用设备制造业企业总资产按各自当前增速+6%（以省内各企业营业收入同比增减幅的中位数作为总资产增速的替代指标）持续扩张，无政策省份则以减半增速计算；情景二（全量减半基准情景）：所有省份不论有无政策，一律按当前增速的一半推算总资产增长。以3年复合增长分别推算两种情景下各省2025年总资产，并以两情景之差作为"政策带来的额外总资产增量"，请问：在出台了上述专项政策且符合最低企业数量门槛的省份中，哪个省份从该政策中撬动的额外总资产增量（额外增量=政策分化情景下2025年总资产 - 全量减半情景下2025年总资产）最为可观？该增量具体为多少亿元？

Output guidelines:
依次回答省份名称和额外总资产增量。额外增量保留2位小数，单位为亿元。如["湖南省", 520.38]。如果无法找到相关数据，请回答"未查询到相关数据"

Only use files under `./database/`.

## Expected Behavior

Agent should read the provided `database/` files, compute the result, and return the final answer. The final answer must follow the required output format.

## Grading Criteria

- [ ] Final answer semantically matches the gold `answer`.
- [ ] Output format follows `guidelines`.

## LLM Judge Rubric

### Criterion 1: Multi-answer Correctness (Weight: 100%)

Gold answer JSON:
`["广东省", 140.38]`

Scoring rules:
- The gold answer is a list with N=2 parts.
- Judge each predicted part against the corresponding gold part by semantic equivalence.
- Return `scores` with `part_0 ... part_1` each as 0 or 1.
- Return `total = (sum(part_i)) / 2` exactly.
- If the model output is missing or cannot be parsed into 2 comparable parts, score all parts 0.

