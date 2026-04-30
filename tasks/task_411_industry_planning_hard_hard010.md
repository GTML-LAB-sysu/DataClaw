---
id: task_411_industry_planning_hard_hard010
name: industry_planning-hard-hard010
category: industry_planning
grading_type: llm_judge
timeout_seconds: 1200
gold_file: qa_gold/industry_planning/hard010.json
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

在铁路、船舶、航空航天和其他运输设备制造业（即广义轨道交通装备制造业）领域，以2022年为基期，构建以下轨道交通政策激励传导模型（轨道交通装备制造相关企业存续数量不低于3家的中国大陆省级行政区，港澳台不计入）：若某省已明确将轨道交通装备产业列入重点打造产业集群目录并配套专项支持措施，则该省企业营业收入的年增速可在现有中位水平上再叠加3个百分点；而未落地此类产业集群专项支持政策的省份，其营业收入增速将在原有基础上收缩30%（增速取省内各企业营业收入同比增减幅中位数）。以上述情景增速进行3年复合增长预测，并计算各有政策省份从2022年到2025年的营业收入绝对增量（定义为：2025年预测营业收入 − 2022年实际营业收入），请问：哪个获得政策支持的省份营业收入的绝对增量最为可观？该省这一增量数值为多少亿元？

Output guidelines:
依次回答省份名称和营业收入绝对增量。绝对增量保留2位小数。如["上海市", 185.42]。如果无法找到相关数据，请回答"未查询到相关数据"

Only use files under `./database/`.

## Expected Behavior

Agent should read the provided `database/` files, compute the result, and return the final answer. The final answer must follow the required output format.

## Grading Criteria

- [ ] Final answer semantically matches the gold `answer`.
- [ ] Output format follows `guidelines`.

## LLM Judge Rubric

### Criterion 1: Multi-answer Correctness (Weight: 100%)

Gold answer JSON:
`["山东省", 413.38]`

Scoring rules:
- The gold answer is a list with N=2 parts.
- Judge each predicted part against the corresponding gold part by semantic equivalence.
- Return `scores` with `part_0 ... part_1` each as 0 or 1.
- Return `total = (sum(part_i)) / 2` exactly.
- If the model output is missing or cannot be parsed into 2 comparable parts, score all parts 0.

