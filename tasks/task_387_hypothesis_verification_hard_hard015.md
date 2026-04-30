---
id: task_387_hypothesis_verification_hard_hard015
name: hypothesis_verification-hard-hard015
category: hypothesis_verification
grading_type: llm_judge
timeout_seconds: 1200
gold_file: qa_gold/hypothesis_verification/hard015.json
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

政策文本的表述精度，即政策目标是以可量化的具体数值呈现，还是以方向性、原则性的定性语言为主，可能反映政府的政策执行意志，进而影响辖区内企业的研发行为。在仪器仪表制造业中，对已出台涉及本行业地方政策的省份进行内容分析：凡政策正文中含有具体产业发展数值目标（如产业规模达X亿元、增长X%、新建X家/X座等可核查数值）的省份，归为量化目标组；政策正文仅涵盖定性方向、原则性要求或门槛条件而不包含上述产业发展数值目标的省份，归为定性目标组。基于2022年数据，请分别计算两组省份内仪器仪表制造业有效企业（研发投入占比数据非空且数值在0%到100%之间）的研发投入占比均值，并给出量化目标组均值减去定性目标组均值的差值（单位：百分点）。

Output guidelines:
依次回答含量化目标省份的研发投入占比均值、仅含定性目标省份的研发投入占比均值、两者差值（量化组均值减去定性组均值）。均值和差值均保留2位小数，以百分点表示。如[12.53, 8.21, 4.32]。如果无法找到相关数据，请回答"未查询到相关数据"

Only use files under `./database/`.

## Expected Behavior

Agent should read the provided `database/` files, compute the result, and return the final answer. The final answer must follow the required output format.

## Grading Criteria

- [ ] Final answer semantically matches the gold `answer`.
- [ ] Output format follows `guidelines`.

## LLM Judge Rubric

### Criterion 1: Multi-answer Correctness (Weight: 100%)

Gold answer JSON:
`[14.07, 9.67, 4.4]`

Scoring rules:
- The gold answer is a list with N=3 parts.
- Judge each predicted part against the corresponding gold part by semantic equivalence.
- Return `scores` with `part_0 ... part_2` each as 0 or 1.
- Return `total = (sum(part_i)) / 3` exactly.
- If the model output is missing or cannot be parsed into 3 comparable parts, score all parts 0.

