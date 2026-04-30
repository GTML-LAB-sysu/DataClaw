---
id: task_385_hypothesis_verification_hard_hard013
name: hypothesis_verification-hard-hard013
category: hypothesis_verification
grading_type: llm_judge
timeout_seconds: 1200
gold_file: qa_gold/hypothesis_verification/hard013.json
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

国家与地方政策的协同效应，在产业经济学中通常以政策叠加框架加以讨论——双重政策覆盖的企业是否在劳动效率上具有系统性优势，是检验政策层级互补性的核心命题之一。人均营业收入作为劳动效率的代理变量，以2022年食品饮料业为例，将企业所在省份按政策覆盖状态分为三组：第一组，省份同时被国家消费品工业促进政策明确列为活动实施省份且已出台地方食品相关产业政策；第二组，省份仅有地方食品相关产业政策、未被前述国家政策明确覆盖；第三组，上述两类政策均无。有效企业须营业收入金额非空且雇员总数为正的内地企业（排除港澳台）。三组企业的平均人均营业收入分别为多少万元？第一组与第二组的均值差为多少万元？

Output guidelines:
依次回答双重覆盖组、仅地方覆盖组、无政策覆盖组的平均人均营业收入（万元/人），以及双重覆盖组与仅地方覆盖组的差值（万元/人）。所有数值保留2位小数。如[185.30, 152.75, 126.40, 32.55]。如果无法找到相关数据，请回答"未查询到相关数据"

Only use files under `./database/`.

## Expected Behavior

Agent should read the provided `database/` files, compute the result, and return the final answer. The final answer must follow the required output format.

## Grading Criteria

- [ ] Final answer semantically matches the gold `answer`.
- [ ] Output format follows `guidelines`.

## LLM Judge Rubric

### Criterion 1: Multi-answer Correctness (Weight: 100%)

Gold answer JSON:
`[201.94, 168.2, 140.96, 33.74]`

Scoring rules:
- The gold answer is a list with N=4 parts.
- Judge each predicted part against the corresponding gold part by semantic equivalence.
- Return `scores` with `part_0 ... part_3` each as 0 or 1.
- Return `total = (sum(part_i)) / 4` exactly.
- If the model output is missing or cannot be parsed into 4 comparable parts, score all parts 0.

