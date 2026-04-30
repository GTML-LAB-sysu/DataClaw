---
id: task_418_industry_planning_medium_medium003
name: industry_planning-medium-medium003
category: industry_planning
grading_type: llm_judge
timeout_seconds: 1200
gold_file: qa_gold/industry_planning/medium003.json
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

Using 2022 as the base period, a differentiated policy incentive is proposed for the automobile manufacturing industry: For provinces that have implemented automobile industry policies containing the keywords "new energy" or "electric", the annual operating profit growth rate of automobile manufacturing enterprises within their jurisdiction will add 10 percentage points on top of the current median growth rate, creating a policy acceleration effect; other provinces are unaffected, and operating profit growth rate continues along the current trajectory. Under this differentiated scenario, using the median year-on-year change in operating profit as the baseline growth rate for each province, and projecting to 2025 via 3-year compound growth, which province has the most prominent increase in total operating profit compared to actual 2022 levels? What is the specific increase (increase = (2025 estimated value - 2022 actual value) / 2022 actual value × 100%)?

Output guidelines:
Answer format: value (2 decimal places, unit: %). If relevant data cannot be found, please answer "No relevant data found".

Only use files under `./database/`.

## Expected Behavior

Agent should read the provided `database/` files, compute the result, and return the final answer. The final answer must follow the required output format.

## Grading Criteria

- [ ] Final answer semantically matches the gold `answer`.
- [ ] Output format follows `guidelines`.

## LLM Judge Rubric

### Criterion 1: Single-answer Correctness (Weight: 100%)

Gold answer JSON:
`859.71`

Scoring rules:
- Judge semantic equivalence between the model final answer and the gold answer.
- Return `scores` with one key `match` as 1 or 0.
- Return `total` as 1.0 if equivalent, otherwise 0.0.

