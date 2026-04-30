---
id: task_384_hypothesis_verification_hard_hard012
name: hypothesis_verification-hard-hard012
category: hypothesis_verification
grading_type: llm_judge
timeout_seconds: 1200
gold_file: qa_gold/hypothesis_verification/hard012.json
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

一个行业内营业利润率的分布离散程度，在一定条件下可反映企业间的竞争分化态势或政策的结构性影响效应。以四分位距（IQR = Q3减去Q1，均基于企业个体营业利润率的分布计算）作为离散程度的测量工具，对2022年橡胶和塑料制品业（排除港澳台）数据进行分析，营业利润率=营业利润金额/营业收入金额×100%。若以出台了面向制造业企业、按发展阶段设定梯度化现金奖励或培育支持机制且将橡胶和塑料制品业列为受益行业的专项产业培育激励政策的省份为一组，其余省份为另一组，两组企业营业利润率的IQR分别是多少个百分点？两组IQR的差值（有政策省份减无政策省份）为多少个百分点？

Output guidelines:
依次回答有政策省份的IQR、无政策省份的IQR、两者差值。数值以百分点表示，保留2位小数。如[5.82, 9.45, -3.63]。如果无法找到相关数据，请回答"未查询到相关数据"

Only use files under `./database/`.

## Expected Behavior

Agent should read the provided `database/` files, compute the result, and return the final answer. The final answer must follow the required output format.

## Grading Criteria

- [ ] Final answer semantically matches the gold `answer`.
- [ ] Output format follows `guidelines`.

## LLM Judge Rubric

### Criterion 1: Multi-answer Correctness (Weight: 100%)

Gold answer JSON:
`[4.37, 11.59, -7.23]`

Scoring rules:
- The gold answer is a list with N=3 parts.
- Judge each predicted part against the corresponding gold part by semantic equivalence.
- Return `scores` with `part_0 ... part_2` each as 0 or 1.
- Return `total = (sum(part_i)) / 3` exactly.
- If the model output is missing or cannot be parsed into 3 comparable parts, score all parts 0.

