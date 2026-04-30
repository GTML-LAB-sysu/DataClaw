---
id: task_486_risk_assessment_medium_medium005
name: risk_assessment-medium-medium005
category: risk_assessment
grading_type: llm_judge
timeout_seconds: 1200
gold_file: qa_gold/risk_assessment/medium005.json
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

2022年，相关部委出台了促进钢铁工业高质量发展的指导意见，明确提出金属冶炼行业研发投入强度力争达到1.5%的政策目标。现聚焦以下范围：同时受到国家层面金属冶炼产业发展政策和地方金属冶炼和压延加工业相关政策覆盖的省份，且该省上市企业总数（以营业收入、营业利润和研发投入数据均不为空、营业收入大于零为准）不低于6家，同时全省总营业利润为正值。在此范围内，模拟地方政府出台强制合规要求——凡研发投入强度（研发投入÷营业收入）未达1.5%门槛的企业，须将研发投入强制补足至1.5%，补足部分直接计入成本并从营业利润中扣除。请问：在符合条件的省份中，哪个省份的企业需要补足的研发投入缺口总量最大？执行该合规要求后，该省金属冶炼和压延加工业的总营业利润预计下降多少个百分点？

Output guidelines:
依次回答省份名称和营业利润下降比例。下降比例以百分数表示，保留2位小数。如["山东省", 3.75]。如果无法找到相关数据，请回答"未查询到相关数据"

Only use files under `./database/`.

## Expected Behavior

Agent should read the provided `database/` files, compute the result, and return the final answer. The final answer must follow the required output format.

## Grading Criteria

- [ ] Final answer semantically matches the gold `answer`.
- [ ] Output format follows `guidelines`.

## LLM Judge Rubric

### Criterion 1: Multi-answer Correctness (Weight: 100%)

Gold answer JSON:
`["江西省", 5.91]`

Scoring rules:
- The gold answer is a list with N=2 parts.
- Judge each predicted part against the corresponding gold part by semantic equivalence.
- Return `scores` with `part_0 ... part_1` each as 0 or 1.
- Return `total = (sum(part_i)) / 2` exactly.
- If the model output is missing or cannot be parsed into 2 comparable parts, score all parts 0.

