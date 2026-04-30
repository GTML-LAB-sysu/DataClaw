---
id: task_064_comprehensive_decision_medium_medium039
name: comprehensive_decision-medium-medium039
category: comprehensive_decision
grading_type: llm_judge
timeout_seconds: 1200
gold_file: qa_gold/comprehensive_decision/medium039.json
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

In 2022, list all indicators for which Guangdong Province's Information Transmission, Software and Information Technology Services industry has mean values superior to the national average, and sort them by advantage magnitude from high to low.

Output guidelines:
Answer format: [Indicator 1, Indicator 2, Indicator 3, ...]. Output only indicator names, separated by commas and spaces, do not add any other explanatory text. If relevant data cannot be found, please answer "No relevant data found"

Only use files under `./database/`.

## Expected Behavior

Agent should read the provided `database/` files, compute the result, and return the final answer. The final answer must follow the required output format.

## Grading Criteria

- [ ] Final answer semantically matches the gold `answer`.
- [ ] Output format follows `guidelines`.

## LLM Judge Rubric

### Criterion 1: Multi-answer Correctness (Weight: 100%)

Gold answer JSON:
`["Mean of year-over-year change in R&D investment ratio", "Mean of year-over-year change in net profit", "Mean of annual PCT patent applications", "Mean of annual PCT invention patent applications", "Mean of government incentive funds and subsidies", "Mean of net profit amount", "Mean of year-over-year change in capitalized R&D investment", "Mean of cumulative PCT patent applications", "Mean of cumulative PCT invention patent applications", "Mean of cumulative citations of all patents", "Mean of cumulative China invention patent grants", "Mean of participation in drafting national standards", "Mean of R&D personnel ratio", "Mean of R&D investment ratio", "Mean of asset-liability ratio"]`

Scoring rules:
- The gold answer is a list with N=15 parts.
- Judge each predicted part against the corresponding gold part by semantic equivalence.
- Return `scores` with `part_0 ... part_14` each as 0 or 1.
- Return `total = (sum(part_i)) / 15` exactly.
- If the model output is missing or cannot be parsed into 15 comparable parts, score all parts 0.

