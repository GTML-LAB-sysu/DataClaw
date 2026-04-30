---
id: task_007_comprehensive_decision_hard_hard001
name: comprehensive_decision-hard-hard001
category: comprehensive_decision
grading_type: llm_judge
timeout_seconds: 1200
gold_file: qa_gold/comprehensive_decision/hard001.json
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

In 2022, a strategic consulting firm was commissioned by a provincial government to quantitatively rank the comprehensive attractiveness of pharmaceutical manufacturing across provinces, in order to identify priority target regions for attracting leading enterprises. The company designed a four-dimensional weighted scoring system: four original indicators—enterprise agglomeration level (weight 30%), R&D expenditure as a share of revenue (weight 30%), regional policy coverage intensity (weight 20%), and R&D human resource penetration rate (weight 20%)—were normalized (min-max) and then weighted to produce a composite score. Among these, agglomeration level is measured by the proportion of enterprises in each province to the national total in pharmaceutical manufacturing; policy intensity is measured by the ratio of relevant policy items in each province to the total number of relevant policies nationwide; and human resource penetration rate is the total number of R&D personnel in each province divided by total employees. What is the specific composite score value of the province with the highest weighted composite score after normalization across provinces?

Output guidelines:
The answer should be a numerical value with 2 decimal places. Output only the number, without units or text. If relevant data cannot be found, please answer "No relevant data found"

Only use files under `./database/`.

## Expected Behavior

Agent should read the provided `database/` files, compute the result, and return the final answer. The final answer must follow the required output format.

## Grading Criteria

- [ ] Final answer semantically matches the gold `answer`.
- [ ] Output format follows `guidelines`.

## LLM Judge Rubric

### Criterion 1: Single-answer Correctness (Weight: 100%)

Gold answer JSON:
`0.92`

Scoring rules:
- Judge semantic equivalence between the model final answer and the gold answer.
- Return `scores` with one key `match` as 1 or 0.
- Return `total` as 1.0 if equivalent, otherwise 0.0.

